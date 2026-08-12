from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.ENVIRONMENT == "development",  # logs SQL in dev only
    pool_pre_ping=True,   # checks connection health before using it
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class all models will inherit from
class Base(DeclarativeBase):
    pass

# Dependency — used in every API route
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
