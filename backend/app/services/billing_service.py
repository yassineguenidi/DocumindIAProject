from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import User
from app.repositories import plan_repository
from app.schemas.document import UsageResponse
from app.services import document_service

SELF_SERVE = {"free", "starter", "business"}  # Enterprise = sur devis


def _switch(db: Session, user: User, code: str) -> UsageResponse:
    plan = plan_repository.get_by_code(db, code)
    if plan is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Offre introuvable")
    company = user.company
    if company.plan_id == plan.id:
        raise HTTPException(status.HTTP_409_CONFLICT, "Vous êtes déjà sur cette offre")
    company.plan_id = plan.id
    db.commit()
    db.refresh(company)
    return document_service.get_usage(db, user)


def change_plan(db: Session, user: User, code: str) -> UsageResponse:
    if code not in SELF_SERVE:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cette offre est disponible sur devis : contactez-nous")
    return _switch(db, user, code)


def cancel(db: Session, user: User) -> UsageResponse:
    if user.company.plan.code == "free":
        raise HTTPException(status.HTTP_409_CONFLICT, "Vous êtes déjà sur l'offre gratuite")
    return _switch(db, user, "free")