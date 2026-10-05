from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_filename: str
    mime_type: str
    size_bytes: int
    status: str
    doc_type: Optional[str] = None
    extracted_data: Optional[Any] = None
    error_message: Optional[str] = None
    created_at: datetime


class DocumentList(BaseModel):
    items: List[DocumentResponse]
    total: int



class UsageResponse(BaseModel):
    plan: str
    quota: Optional[int]
    used: int
    remaining: Optional[int]
    period_start: datetime
    max_file_size_mb: int


class ActivityPoint(BaseModel):
    date: str
    count: int


class StatsResponse(BaseModel):
    total: int
    in_progress: int
    done: int
    failed: int
    activity: List[ActivityPoint]  # 14 derniers jours    