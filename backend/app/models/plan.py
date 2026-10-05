from typing import Optional
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base

class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)  # free, starter, business, enterprise
    name: Mapped[str] = mapped_column(String(50))
    monthly_doc_quota: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # None = illimité
    max_file_size_mb: Mapped[int] = mapped_column(Integer, default=10)

    