import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Correct database URL with 'postgresql' dialect
SQLALCHEMY_DATABASE_URL = "postgresql://postgres.focjhzkdbxgwjcdrfeuo:Thequickbrownfox99@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"

# Create the SQLAlchemy engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our ORM models
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
