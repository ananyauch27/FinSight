from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.config import settings
from app.deps import get_db, get_current_user
from app.models import User, RefreshToken
from app.security import (hash_password, verify_password, create_access_token,
                          new_refresh_token, hash_refresh)

router = APIRouter(tags=["auth"])

class RegisterIn(BaseModel):
    email : EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = None

class LoginIn(BaseModel):
     email: EmailStr 
     password: str

class RefreshIn(BaseModel):
     refresh_token: str

def issue_tokens(db: Session, user: User) -> dict:
    raw, hashed = new_refresh_token()
    db.add(RefreshToken(
        user_id=user.id,
        token_hash=hashed,
        expires_at=datetime.now(timezone.utc) +
          timedelta(days=settings.REFRESH_TOKEN_DAYS),
    ))

    db.commit()
    return {"access_token": create_access_token(str(user.id)),
            "refresh_token": raw,
            "token_type": "bearer"}

@router.post("/auth/register", #status_code = 201
             )
def register(body: RegisterIn,
              db: Session = Depends(get_db)):
     if db.query(User).filter(func.lower(User.email) == body.email.lower()).first():
          raise HTTPException(409, "email already registerd")

     user = User(email = body.email.lower(), 
                 password_hash = hash_password(body.password),
                 full_name = body.full_name)

     db.add(user)
     db.commit()
     db.refresh(user)

     return{ "id" : str(user.id),
            "email" : user.email,
            "full_name" :user.full_name}


@router.post("/auth/login")
def login(body: LoginIn,
           db: Session = Depends(get_db)):
     user = db.query(User).filter(User.email == body.email.lower()).first()
   
     if not user or not verify_password(body.password, user.password_hash):
          raise HTTPException(401, "Invalid email or password")
   
     return issue_tokens(db, user)

@router.post("/auth/refresh")
def refresh(body: RefreshIn,
             db: Session = Depends(get_db)):
    row = db.query(RefreshToken).filter_by(token_hash=hash_refresh(body.refresh_token), 
                                           revoked=False).first()
    
    if not row or row.expires_at < datetime.now(timezone.utc):
        raise HTTPException(401, "Invalid refresh token")
   
    row.revoked = True                      
    user = db.get(User, row.user_id)
    return issue_tokens(db, user)    

@router.post("/auth/logout")
def logout(body: RefreshIn,
            db: Session = Depends(get_db)):
    row = db.query(RefreshToken).filter_by(token_hash=hash_refresh(body.refresh_token)).first()
    if row:
        row.revoked = True; db.commit()
    
    return {"ok": True}

@router.get("/auth/me")
def me(user: User = Depends(get_current_user)):
    return {"id": str(user.id), "email": user.email, "full_name": user.full_name, "currency": user.currency}

@router.delete("/auth/me", status_code=204)
def delete_me(db: Session = Depends(get_db),
               user: User = Depends(get_current_user)):
    db.delete(user); db.commit() 