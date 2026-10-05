from typing import Optional
from sqlalchemy.orm import Session
from app.models import User


def get_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email.lower()).first()


def get_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def get_by_google_sub(db: Session, sub: str) -> Optional[User]:
    return db.query(User).filter(User.google_sub == sub).first()