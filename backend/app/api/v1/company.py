import re
import secrets

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.config import settings
from app.db import get_db
from app.models import User
from app.services import email_intake

router = APIRouter(prefix="/company", tags=["company"])
SENDER_RE = re.compile(r"@[a-z0-9.-]+\.[a-z]{2,}|[^@\s]+@[a-z0-9.-]+\.[a-z]{2,}")


class InboxUpdate(BaseModel):
    allowed: str = Field("", max_length=2000)


def _view(company) -> dict:
    return {
        "enabled": email_intake.enabled(),
        "address": email_intake.address_for(company.inbox_token) if company.inbox_token else None,
        "allowed": company.inbox_allowed or "",
        "require_auth": settings.INBOX_REQUIRE_AUTH,
    }


@router.get("/inbox")
def get_inbox(user: User = Depends(require_admin), db: Session = Depends(get_db)):
    company = user.company
    if not company.inbox_token:
        company.inbox_token = secrets.token_hex(8)
        db.commit()
        db.refresh(company)
    return _view(company)


@router.put("/inbox")
def update_inbox(data: InboxUpdate, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    entries = [e.lower() for e in re.split(r"[,;\s]+", data.allowed) if e]
    bad = [e for e in entries if not SENDER_RE.fullmatch(e)]
    if bad:
        raise HTTPException(422, f"Entrée invalide : « {bad[0]} » (utilisez une adresse ou un domaine du type @exemple.fr)")
    company = user.company
    company.inbox_allowed = "\n".join(dict.fromkeys(entries))
    db.commit()
    db.refresh(company)
    return _view(company)


@router.post("/inbox/rotate")
def rotate_inbox(user: User = Depends(require_admin), db: Session = Depends(get_db)):
    company = user.company
    company.inbox_token = secrets.token_hex(8)  # l'ancienne adresse cesse de fonctionner
    db.commit()
    db.refresh(company)
    return _view(company)