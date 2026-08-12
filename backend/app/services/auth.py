import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.sevak import Sevak, SevakStatusEnum, AccountEvent, RoleEnum
from app.core.security import (
    verify_password,
    create_access_token,
    hash_password,
    decode_access_token
)
from app.services.attendance import get_local_now
from app.services.email_identity import normalize_email
from app.services.notifications import create_password_reset_notification, send_account_activation_email

logger = logging.getLogger(__name__)


def get_max_failed_attempts(db: Session) -> int:
    """Get max failed login attempts from system config."""
    from app.models.department import SystemConfig
    config = db.query(SystemConfig).filter(
        SystemConfig.key == "MAX_FAILED_LOGIN_ATTEMPTS"
    ).first()
    return int(config.value) if config else 3  # default 3


def authenticate_sevak(
    db: Session,
    identifier: str | None = None,
    password: str = "",
    ip_address: str = None,
    sevak_id: int | None = None,
) -> Sevak:
    """Authenticate a Sevak by numeric ID or email and password."""

    # Determine if identifier is numeric Sevak ID or email
    identifier = str(identifier if identifier is not None else sevak_id or "").strip()
    if not identifier:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid ID or password."
        )
    if identifier.isdigit():
        sevak = db.query(Sevak).filter(Sevak.sevak_id == int(identifier)).first()
    else:
        from sqlalchemy import func

        sevak = db.query(Sevak).filter(func.lower(Sevak.email) == normalize_email(identifier)).first()

    # Log failed attempt helper
    def log_failed_attempt():
        event = AccountEvent(
            sevak_id=sevak.id if sevak else "unknown",
            event_type="LOGIN_FAILED",
            ip_address=ip_address,
        )
        db.add(event)
        db.commit()

    # Sevak not found
    if not sevak:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid ID or password."
        )

    # Account locked
    if sevak.status == SevakStatusEnum.LOCKED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is locked. Please contact Admin."
        )

    # Account deactivated (inactive) — cannot login
    if sevak.status == SevakStatusEnum.INACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not yet activated. Please click the activation link sent to your inbox."
        )

    # Wrong password
    if not verify_password(password, sevak.hashed_password):
        # Admin and SuperAdmin are never locked out
        if sevak.role in [RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN]:
            log_failed_attempt()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid ID or password."
            )

        max_attempts = get_max_failed_attempts(db)
        sevak.failed_login_attempts += 1

        # Lock account if max attempts reached
        if sevak.failed_login_attempts >= max_attempts:
            sevak.status = SevakStatusEnum.LOCKED
            db.commit()

            # Log lock event
            lock_event = AccountEvent(
                sevak_id=sevak.id,
                event_type="LOCKED",
                ip_address=ip_address,
                notes=f"Auto-locked after {max_attempts} failed attempts"
            )
            db.add(lock_event)
            db.commit()

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"All of the {max_attempts} attempts have been failed. Please contact Admin to unlock your account."
            )

        db.commit()
        log_failed_attempt()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid ID or password. "
                   f"{max_attempts - sevak.failed_login_attempts} attempts remaining."
        )

    if not sevak.email_verified and sevak.email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email address is not verified. Please click the activation link sent to your inbox."
        )

    # Successful login — reset failed attempts
    sevak.failed_login_attempts = 0
    sevak.last_login = get_local_now()
    db.commit()

    return sevak


def generate_token(sevak: Sevak) -> dict:
    """Generate JWT token for authenticated sevak."""
    token = create_access_token(data={"sub": sevak.id})
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": sevak.role,
        "sevak_id": sevak.sevak_id,
        "full_name": f"{sevak.first_name} {sevak.last_name}"
    }


def change_password(
    db: Session,
    sevak: Sevak,
    current_password: str,
    new_password: str
) -> bool:
    """Change password after verifying current password."""
    if not verify_password(current_password, sevak.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect."
        )
    sevak.hashed_password = hash_password(new_password)
    sevak.updated_at = get_local_now()
    db.commit()
    return True


def reset_password_with_token(
    db: Session,
    sevak_id: str,
    token: str,
    new_password: str
) -> bool:
    """Verify reset token and update password."""
    sevak = validate_reset_password_token(db=db, sevak_id=sevak_id, token=token)

    sevak.hashed_password = hash_password(new_password)
    sevak.failed_login_attempts = 0
    sevak.status = SevakStatusEnum.ACTIVE
    sevak.updated_at = get_local_now()

    # Log reset event
    event = AccountEvent(
        sevak_id=sevak.id,
        event_type="PASSWORD_RESET_COMPLETED",
        notes="Password reset using email token"
    )
    db.add(event)
    db.commit()
    return True


def validate_reset_password_token(
    db: Session,
    sevak_id: str,
    token: str,
) -> Sevak:
    """Validate a password reset token and return the matching Sevak."""
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset link is invalid or has expired."
        )

    if payload.get("purpose") != "reset_password":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset link is invalid or has expired."
        )

    if str(payload.get("sub")) != str(sevak_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset link is invalid or has expired."
        )

    sevak = db.query(Sevak).filter(Sevak.id == sevak_id).first()
    if not sevak:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reset link is invalid or has expired."
        )

    # Enforce single active link: token must be the most recently issued one
    token_iat = payload.get("iat")
    if token_iat is not None and sevak.password_reset_token_issued_at is not None:
        from datetime import timezone
        # JWT iat is a Unix timestamp; convert stored datetime to timestamp for comparison
        stored_ts = sevak.password_reset_token_issued_at.replace(tzinfo=timezone.utc).timestamp()
        if token_iat < stored_ts - 2:  # 2-second tolerance for clock skew
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This reset link has been invalidated because a newer link was generated. Please use the most recent link sent to your email."
            )
    elif sevak.password_reset_token_issued_at is not None and token_iat is None:
        # Old token without iat, but tracking is enabled → reject
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset link has been invalidated because a newer link was generated. Please use the most recent link sent to your email."
        )

    return sevak


def activate_account_with_token(
    db: Session,
    sevak_id: str,
    token: str,
) -> dict:
    from app.services.sevak import get_next_sevak_id

    sevak = validate_account_activation_token(db=db, sevak_id=sevak_id, token=token)

    # If first time activation, activate account and allocate sevak_id
    is_first_activation = not sevak.email_verified

    sevak.email_verified = True
    sevak.status = SevakStatusEnum.ACTIVE
    sevak.updated_at = get_local_now()
    sevak.activated_at = get_local_now()

    # Allocate sevak_id if not already allocated. Pending onboarding accounts use <= 0 placeholders.
    if sevak.sevak_id is None or sevak.sevak_id <= 0:
        sevak.sevak_id = get_next_sevak_id(db)

    event = AccountEvent(
        sevak_id=sevak.id,
        event_type="ACCOUNT_ACTIVATED",
        notes="Account activated via email link - Sevak ID allocated"
    )
    db.add(event)
    db.commit()

    # Generate login token so user is auto-logged in
    access_token = create_access_token(data={"sub": sevak.id})

    return {
        "success": True,
        "sevak_id": sevak.sevak_id,
        "access_token": access_token,
        "token_type": "bearer",
        "role": sevak.role,
        "full_name": f"{sevak.first_name} {sevak.last_name}",
        "message": f"Account activated successfully! Your Sevak ID is {sevak.sevak_id}."
    }


def validate_account_activation_token(
    db: Session,
    sevak_id: str,
    token: str,
) -> Sevak:
    """Validate an account activation token and return the matching Sevak."""
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account activation link is invalid or has expired."
        )

    if payload.get("purpose") != "activate_account":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account activation link is invalid or has expired."
        )

    if str(payload.get("sub")) != str(sevak_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account activation link is invalid or has expired."
        )

    sevak = db.query(Sevak).filter(Sevak.id == sevak_id).first()
    if not sevak:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account activation link is invalid or has expired."
        )

    return sevak


def verify_email_with_token(db: Session, sevak_id: str, token: str) -> bool:
    """Backward-compatible email verification used by existing tests and older links."""
    payload = decode_access_token(token)
    if not payload or payload.get("purpose") != "verify_email" or str(payload.get("sub")) != str(sevak_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email verification link is invalid or has expired."
        )

    sevak = db.query(Sevak).filter(Sevak.id == sevak_id).first()
    if not sevak:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email verification link is invalid or has expired."
        )

    sevak.email_verified = True
    sevak.updated_at = get_local_now()
    event = AccountEvent(
        sevak_id=sevak.id,
        event_type="EMAIL_VERIFIED",
        notes="Email verified using legacy verification token",
    )
    db.add(event)
    db.commit()
    return True


def resend_activation_email(db: Session, sevak: Sevak, requested_by_name: str | None = None) -> bool:
    if not sevak.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sevak does not have an email address configured."
        )
    if sevak.email_verified:
        return True
    return send_account_activation_email(db=db, sevak=sevak, requested_by_name=requested_by_name)
