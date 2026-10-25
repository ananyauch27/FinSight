import numpy as np
from collections import defaultdict
from datetime import timedelta
from app.models import Transaction, Merchant
from app.services.repo import create_alert

FREQUENCIES = {          # name: (expected_days, tolerance_days)
    "weekly": (7, 1),
    "monthly": (30, 4),
    "quarterly": (91, 7),
    "yearly": (365, 10),
}

def detect_series(txns):
    """txns: list of (date, amount) for ONE merchant, sorted by date."""
    if len(txns) < 3:
        return None
    dates = [t[0] for t in txns]
    amounts = np.array([float(t[1]) for t in txns])
    gaps = np.diff([d.toordinal() for d in dates])
    median_gap = float(np.median(gaps))

    for name, (days, tol) in FREQUENCIES.items():
        if abs(median_gap - days) <= tol:
            fit = np.mean([abs(g - days) <= tol * 2 for g in gaps])
            if fit < 0.7:
                continue
            med_amt = float(np.median(amounts))
            consistent = np.mean(np.abs(amounts - med_amt) <= 0.15 * med_amt)
            if consistent < 0.6 and name != "monthly":
                continue
            last_amt, prev_amt = amounts[-1], amounts[-2]
            return {
                "frequency": name,
                "typical_amount": round(med_amt, 2),
                "last_amount": round(float(last_amt), 2),
                "last_date": dates[-1],
                "next_expected": dates[-1] + timedelta(days=days),
                "occurrences": len(txns),
                "price_changed": abs(last_amt - prev_amt) / prev_amt > 0.05,
            }
    return None

def upsert_recurring_series(db, user_id, merchant_id, r: dict):
    m = db.get(Merchant, merchant_id)
    if m.recurring_status == "ignored":
        return
    was_new = m.recurring_frequency is None
    old_price_flag = m.price_changed

    m.recurring_frequency = r["frequency"]
    m.typical_amount = r["typical_amount"]
    m.last_amount = r["last_amount"]
    m.last_date = r["last_date"]
    m.next_expected = r["next_expected"]
    m.occurrences = r["occurrences"]
    m.price_changed = r["price_changed"]

    (db.query(Transaction)
       .filter_by(user_id=user_id, merchant_id=merchant_id)
       .update({"is_recurring": True}, synchronize_session=False))

    if was_new:
        create_alert(db, user_id, "new_subscription", "info", f"New recurring payment: {m.name}",
                     f"{m.name} looks like a {r['frequency']} payment of about ₹{r['typical_amount']:,.0f}.")
    if r["price_changed"] and not old_price_flag:
        create_alert(db, user_id, "price_hike", "warning", f"Price change: {m.name}",
                     f"Latest charge ₹{r['last_amount']:,.0f} differs from your usual ₹{r['typical_amount']:,.0f}.")

def detect_recurring(db, user_id):
    by_merchant = defaultdict(list)
    q = (db.query(Transaction.merchant_id, Transaction.txn_date, Transaction.amount)
           .filter(Transaction.user_id == user_id, Transaction.direction == "debit",
                   Transaction.merchant_id.isnot(None))
           .order_by(Transaction.txn_date))
    for merchant_id, d, amt in q:
        by_merchant[merchant_id].append((d, amt))

    for merchant_id, items in by_merchant.items():
        result = detect_series(items)
        if result:
            upsert_recurring_series(db, user_id, merchant_id, result)
    db.commit()