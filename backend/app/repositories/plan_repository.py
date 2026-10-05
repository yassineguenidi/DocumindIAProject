from typing import Optional, List
from sqlalchemy.orm import Session
from app.models import Plan


def get_by_code(db: Session, code: str) -> Optional[Plan]:
    return db.query(Plan).filter(Plan.code == code).first()

def list_all(db: Session) -> List[Plan]:
    return db.query(Plan).order_by(Plan.id).all()