import os
from datetime import datetime, timezone
from uuid import uuid4
from app.database import SessionLocal
from app.models import Upload, Merchant
from app.services.parsers.registry import pick_parser
from app.services.normalizer import to_merchant_name, clean_description
from app.services.categorizer import categorize
from app.services.dedupe import make_hash, bulk_insert_ignore_duplicates
from app.services.repo import category_map, get_or_create_merchant
from app.services.rules import load_user_rules
from app.services.recurring_detector import detect_recurring
from app.services.anomaly_detector import detect_anomalies
from app.services.analytics import check_budgets

def remove_file_quietly(path):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except PermissionError:
        pass          # Windows may briefly lock the file (antivirus); safe to leave it

def process_upload(upload_id: str, pdf_password: str | None):
    db = SessionLocal()
    stored_path = None
    try:
        up = db.get(Upload, upload_id)
        stored_path = up.stored_path
        user_id, account_id = up.user_id, up.account_id
        up.status = "processing"; db.commit()

        parser = pick_parser(up.filename)
        up.detected_bank = parser.bank_code
        parsed = parser.parse(stored_path, pdf_password)       # list[ParsedTxn]
        up.rows_total = len(parsed)

        merchants = {m.name.lower(): m for m in db.query(Merchant).filter_by(user_id=user_id)}
        known_names = [m.name for m in merchants.values()]
        alias_rows = [(m.name, m.aliases) for m in merchants.values() if m.aliases]
        rules = load_user_rules(db, user_id)                   # {merchant_lower: category_name}
        cats = category_map(db, user_id)                       # {category_lower: id}
        uncategorized = cats["uncategorized"]

        rows = []
        for t in parsed:
            name = to_merchant_name(t.description, known_names, alias_rows)
            merchant = get_or_create_merchant(db, user_id, name, merchants)
            clean = clean_description(t.description)
            cat_name, source, conf = categorize(name, clean, rules)
            rows.append(dict(
                id=uuid4(), user_id=user_id, account_id=account_id, upload_id=up.id,
                txn_date=t.txn_date, raw_description=t.description, clean_description=clean,
                merchant_id=merchant.id,
                category_id=cats.get(cat_name.lower(), uncategorized),
                amount=t.amount, direction=t.direction, balance_after=t.balance,
                reference_no=t.reference, category_source=source, category_conf=conf,
                dedupe_hash=make_hash(account_id, t),
            ))

        inserted = bulk_insert_ignore_duplicates(db, rows)
        up.rows_inserted, up.rows_duplicate = inserted, len(rows) - inserted
        db.commit()

        detect_recurring(db, user_id)
        detect_anomalies(db, user_id)
        check_budgets(db, user_id)

        up.status = "done"
        up.completed_at = datetime.now(timezone.utc)
        db.commit()
    except Exception as e:
        db.rollback()
        up = db.get(Upload, upload_id)
        up.status, up.error_message = "failed", str(e)[:500]
        db.commit()
    finally:
        db.close()
        remove_file_quietly(stored_path)      # never keep raw statements on disk