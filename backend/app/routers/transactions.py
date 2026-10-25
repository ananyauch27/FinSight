from datetime import date
from decimal import Decimal
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload
from app.deps import get_db, get_current_user
from app.models import Transaction, Category, User
from app.services.rules import apply_correction

router = APIRouter(tags=["transactions"])

# ---------- schemas ----------
class MerchantMini(BaseModel):
    id: UUID
    name: str
    model_config = ConfigDict(from_attributes=True)

class CategoryMini(BaseModel):
    id: UUID
    name: str
    model_config = ConfigDict(from_attributes=True)

class TransactionOut(BaseModel):
    id: UUID
    txn_date: date
    raw_description: str
    clean_description: str | None
    merchant: MerchantMini | None
    category: CategoryMini | None
    amount: Decimal
    direction: str
    is_recurring: bool
    is_anomaly: bool
    category_source: str
    category_conf: float | None
    tags: list[str]
    splits: list | None
    notes: str | None
    model_config = ConfigDict(from_attributes=True)

class TxnPatch(BaseModel):
    category_id: UUID | None = None
    apply_to_similar: bool = False
    notes: str | None = None
    tags: list[str] | None = None

class SplitIn(BaseModel):
    category_id: UUID
    amount: Decimal = Field(gt=0)

# ---------- helpers ----------
def owned_txn(db: Session, user: User, txn_id: UUID) -> Transaction:
    t = (db.query(Transaction).options(joinedload(Transaction.merchant), joinedload(Transaction.category))
           .filter(Transaction.id == txn_id, Transaction.user_id == user.id).first())
    if not t:
        raise HTTPException(404, "Transaction not found")
    return t

def visible_category(db: Session, user: User, category_id: UUID) -> Category:
    c = db.query(Category).filter(Category.id == category_id,
                                  or_(Category.user_id.is_(None), Category.user_id == user.id)).first()
    if not c:
        raise HTTPException(422, "Unknown category")
    return c

SORTABLE = {"txn_date": Transaction.txn_date, "amount": Transaction.amount, "created_at": Transaction.created_at}

# ---------- list ----------
@router.get("/transactions")
def list_transactions(
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
    date_from: date | None = None, date_to: date | None = None,
    category_id: UUID | None = None, merchant_id: UUID | None = None, account_id: UUID | None = None,
    direction: str | None = Query(None, pattern="^(debit|credit)$"),
    min_amount: Decimal | None = None, max_amount: Decimal | None = None,
    q_text: str | None = Query(None, alias="q"), tag: str | None = None,
    anomalies_only: bool = False, recurring_only: bool = False,
    sort: str = "-txn_date",
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    q = (db.query(Transaction)
           .options(joinedload(Transaction.merchant), joinedload(Transaction.category))
           .filter(Transaction.user_id == user.id))
    if date_from: q = q.filter(Transaction.txn_date >= date_from)
    if date_to: q = q.filter(Transaction.txn_date <= date_to)
    if category_id: q = q.filter(Transaction.category_id == category_id)
    if merchant_id: q = q.filter(Transaction.merchant_id == merchant_id)
    if account_id: q = q.filter(Transaction.account_id == account_id)
    if direction: q = q.filter(Transaction.direction == direction)
    if min_amount is not None: q = q.filter(Transaction.amount >= min_amount)
    if max_amount is not None: q = q.filter(Transaction.amount <= max_amount)
    if q_text:
        like = f"%{q_text}%"
        q = q.filter(or_(Transaction.raw_description.ilike(like), Transaction.clean_description.ilike(like)))
    if tag: q = q.filter(Transaction.tags.contains([tag.lower()]))      # uses the GIN index
    if anomalies_only: q = q.filter(Transaction.is_anomaly.is_(True))
    if recurring_only: q = q.filter(Transaction.is_recurring.is_(True))

    total = q.count()
    col = SORTABLE.get(sort.lstrip("-"), Transaction.txn_date)
    order = col.desc() if sort.startswith("-") else col.asc()
    items = q.order_by(order, Transaction.id).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [TransactionOut.model_validate(t) for t in items],
            "page": page, "page_size": page_size, "total": total}

@router.get("/transactions/{txn_id}", response_model=TransactionOut)
def get_transaction(txn_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return owned_txn(db, user, txn_id)

# ---------- edit: category correction, notes, tags ----------
@router.patch("/transactions/{txn_id}", response_model=TransactionOut)
def patch_transaction(txn_id: UUID, body: TxnPatch,
                      db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    t = owned_txn(db, user, txn_id)
    fields = body.model_fields_set

    if "notes" in fields:
        t.notes = body.notes
    if "tags" in fields and body.tags is not None:
        t.tags = sorted({x.strip().lower() for x in body.tags if x.strip()})
    if body.category_id:
        visible_category(db, user, body.category_id)
        apply_correction(db, user, t, body.category_id, body.apply_to_similar)   # commits
    else:
        db.commit()
    db.refresh(t)
    return t

# ---------- splits (stored as JSONB on the transaction) ----------
@router.put("/transactions/{txn_id}/splits", response_model=TransactionOut)
def set_splits(txn_id: UUID, body: list[SplitIn],
               db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    t = owned_txn(db, user, txn_id)
    if len(body) < 2:
        raise HTTPException(422, "A split needs at least two parts")
    for s in body:
        visible_category(db, user, s.category_id)               # replaces a foreign-key check
    if sum(s.amount for s in body) != t.amount:
        raise HTTPException(422, "Splits must add up to the transaction amount")
    t.splits = [{"category_id": str(s.category_id), "amount": str(s.amount)} for s in body]
    db.commit(); db.refresh(t)
    return t

@router.delete("/transactions/{txn_id}/splits", response_model=TransactionOut)
def clear_splits(txn_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    t = owned_txn(db, user, txn_id)
    t.splits = None                                             # stored as SQL NULL (none_as_null=True)
    db.commit(); db.refresh(t)
    return t