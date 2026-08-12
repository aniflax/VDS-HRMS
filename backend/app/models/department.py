import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, Enum as SAEnum, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
import enum
from app.core.timezone import get_local_now


class ConfigAccessLevel(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    HR = "HR"


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=True)
    hod_id: Mapped[str] = mapped_column(String(36), nullable=True)
    location_lat: Mapped[float] = mapped_column(Float, nullable=True)
    location_lng: Mapped[float] = mapped_column(Float, nullable=True)
    geo_threshold_meters: Mapped[int] = mapped_column(
        Integer, default=500
    )
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=get_local_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=get_local_now, onupdate=get_local_now
    )


class SystemConfig(Base):
    __tablename__ = "system_config"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    key: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )
    value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    access_level: Mapped[ConfigAccessLevel] = mapped_column(
        SAEnum(ConfigAccessLevel), nullable=False
    )
    modified_by: Mapped[str] = mapped_column(String(36), nullable=True)
    modified_at: Mapped[datetime] = mapped_column(
        DateTime, default=get_local_now, onupdate=get_local_now
    )