from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt
from app.database import get_db
from app.security import decode_token
from app.models import User

bearer = HTTPBearer()

def get_current_user(
        creds: HTTPAuthorizationCredentials = Depends(bearer),
          db: Session = Depends(get_db) ) -> User:
        try:
               payload = decode_token(creds.credentials)
               if payload.get("type") != "access":
                 raise HTTPException(401, "Invalid token type")
        except jwt.PyJWTError: 
            raise HTTPException(401, "Invalid or expired token") 
        
        user = db.get(User, payload["sub"])
        if not user: raise HTTPException(401, "User not found") 
        
        return user
