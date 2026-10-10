from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow():
    return datetime.now(timezone.utc)


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    inbox_token: Mapped[Optional[str]] = mapped_column(String(32), unique=True, index=True, nullable=True)
    inbox_allowed: Mapped[str] = mapped_column(Text, default="", server_default="")  # expéditeurs autorisés en plus des utilisateurs

    plan = relationship("Plan")
    users = relationship("User", back_populates="company")
    documents = relationship("Document", back_populates="company")