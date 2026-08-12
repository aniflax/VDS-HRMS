import uuid
from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.core.timezone import get_local_now

class SystemConfig(Base):
    __tablename__ = "system_config"
    __table_args__ = {'extend_existing': True}

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    access_level: Mapped[str] = mapped_column(String(50), nullable=True)
    modified_by: Mapped[str] = mapped_column(String(36), nullable=True)
    modified_at: Mapped[datetime] = mapped_column(DateTime, default=get_local_now, onupdate=get_local_now)