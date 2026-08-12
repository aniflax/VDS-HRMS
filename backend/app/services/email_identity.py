from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.sevak import Sevak


def normalize_email(email: str | None) -> str | None:
    if email is None:
        return None
    normalized = email.strip().lower()
    return normalized or None


def find_sevak_by_email(
    db: Session,
    email: str | None,
    *,
    exclude_sevak_id: str | None = None,
) -> Sevak | None:
    normalized_email = normalize_email(email)
    if not normalized_email:
        return None

    query = db.query(Sevak).filter(func.lower(Sevak.email) == normalized_email)
    if exclude_sevak_id:
        query = query.filter(Sevak.id != exclude_sevak_id)
    return query.first()


def ensure_email_available(
    db: Session,
    email: str | None,
    *,
    exclude_sevak_id: str | None = None,
) -> str | None:
    normalized_email = normalize_email(email)
    if normalized_email and find_sevak_by_email(db, normalized_email, exclude_sevak_id=exclude_sevak_id):
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail="Email already registered")
    return normalized_email
