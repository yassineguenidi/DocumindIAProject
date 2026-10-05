from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.db import get_db
from app.models import User
from app.repositories import plan_repository
from app.schemas.billing import ChangePlanRequest, PlanResponse
from app.schemas.document import UsageResponse
from app.services import billing_service

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/plans", response_model=List[PlanResponse])
def plans(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return plan_repository.list_all(db)


@router.post("/change-plan", response_model=UsageResponse)
def change_plan(data: ChangePlanRequest, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    return billing_service.change_plan(db, user, data.plan_code)


@router.post("/cancel", response_model=UsageResponse)
def cancel(user: User = Depends(require_admin), db: Session = Depends(get_db)):
    return billing_service.cancel(db, user)