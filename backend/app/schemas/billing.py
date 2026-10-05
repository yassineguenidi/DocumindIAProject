from typing import Optional

from pydantic import BaseModel, ConfigDict


class PlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    monthly_doc_quota: Optional[int]
    max_file_size_mb: int


class ChangePlanRequest(BaseModel):
    plan_code: str