import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing from backend/ .env")

if DATABASE_URL.startswith("postgres://"): 
      DATABASE_URL = DATABASE_URL.replace(
        "postgres://", "postgresql+psycopg://", 1
    )
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://", "postgresql+psycopg://", 1
    )

engine = create_engine(
     DATABASE_URL,
     pool_pre_ping=True,
)

Sessionlocal = sessionmaker(
     bind = engine,
     autofush = False,
     autocommit = False
)

class Base(DeclarativeBase):
     pass

def get_db():
     db = Sessionlocal()
     try:
          yield db

     finally:
          db.close()