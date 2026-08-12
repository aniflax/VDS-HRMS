import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Float, Boolean, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.core.timezone import get_local_now


class Location(Base):
    """Master location table - managed by SuperAdmin only."""
    __tablename__ = "locations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(
        String(200), nullable=False, unique=True
    )
    address: Mapped[str] = mapped_column(
        Text, nullable=True
    )
    latitude: Mapped[float] = mapped_column(
        Float, nullable=False
    )
    longitude: Mapped[float] = mapped_column(
        Float, nullable=False
    )
    geo_threshold_meters: Mapped[int] = mapped_column(
        Integer, default=500
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=get_local_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=get_local_now, onupdate=get_local_now
    )
