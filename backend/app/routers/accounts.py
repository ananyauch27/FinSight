from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session
from app.deps import get_db, get_current_user
from app.models import Account, User

router = APIRouter(tags=["accounts"])

class AccountIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    bank_code: str | None = None
    account_type: str = "savings"
    last4: str | None = Field(None, min_length=4, max_length=4)

class AccountOut(AccountIn):
    id: UUID
    model_config = ConfigDict(from_attributes=True)

def owned_account(db: Session, user: User, account_id: UUID) -> Account:
    acc = db.query(Account).filter_by(id=account_id, 
                                      user_id=user.id).first()
    if not acc:
        raise HTTPException(404, "Account not found")      # 404, not 403: don't reveal it exists
    return acc

@router.get("/accounts", response_model=list[AccountOut])
def list_accounts(db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
    
    return db.query(Account).filter_by(user_id = user.id).order_by(Account.created_at).all()

@router.post("/accounts", response_model=AccountOut, status_code=201)
def create_account(body: AccountIn,
                    db: Session = Depends(get_db), 
                    user: User = Depends(get_current_user)):
    acc = Account(user_id=user.id,
                   **body.model_dump())
    
    db.add(acc)
    db.commit()
    db.refresh(acc)
    return acc

@router.patch("/accounts/{account_id}", response_model=AccountOut)
def update_account(account_id: UUID,
                    body: AccountIn, 
                    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)):
    acc = owned_account(db, user, account_id)
    for k, v in body.model_dump().items():
        setattr(acc, k, v)
    db.commit()
    db.refresh(acc)
    return acc

@router.delete("/accounts/{account_id}", status_code=204)
def delete_account(account_id: UUID, 
                   db: Session = Depends(get_db), 
                   user: User = Depends(get_current_user)):
    db.delete(owned_account(db, user, account_id))
    db.commit()