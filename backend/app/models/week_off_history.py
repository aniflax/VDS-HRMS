import uuid
from datetime import datetime, date

from sqlalchemy import Date, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.timezone import get_local_now


class SevakWeekOffHistory(Base):
    __tablename__ = "sevak_week_off_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sevak_id: Mapped[str] = mapped_column(String(36), ForeignKey("sevaks.id"), nullable=False)
    week_off_day: Mapped[str] = mapped_column(String(20), nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_local_now)
