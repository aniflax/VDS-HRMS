from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.sevak import Sevak, RoleEnum, SevakStatusEnum

# DB dependency
DbSession = Annotated[Session, Depends(get_db)]

# OAuth2 scheme — looks for token in Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_sevak(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DbSession
) -> Sevak:
    """Get currently logged in Sevak from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    sevak_id: str = payload.get("sub")
    if sevak_id is None:
        raise credentials_exception

    sevak = db.query(Sevak).filter(Sevak.id == sevak_id).first()
    if sevak is None:
        raise credentials_exception

    if sevak.status == SevakStatusEnum.LOCKED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is locked. Please contact Admin."
        )

    if not sevak.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive."
        )

    return sevak


# Role-based access dependencies
CurrentSevak = Annotated[Sevak, Depends(get_current_sevak)]


def require_roles(*roles: RoleEnum):
    """Dependency factory — restricts access to specific roles."""
    def role_checker(
        current_sevak: Annotated[Sevak, Depends(get_current_sevak)]
    ) -> Sevak:
        if current_sevak.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action."
            )
        return current_sevak
    return role_checker


# Pre-built role dependencies — use these in routes
RequireSuperAdmin = Depends(require_roles(RoleEnum.SUPER_ADMIN))

RequireAdmin = Depends(require_roles(
    RoleEnum.SUPER_ADMIN,
    RoleEnum.ADMIN
))

RequireHR = Depends(require_roles(
    RoleEnum.SUPER_ADMIN,
    RoleEnum.ADMIN,
    RoleEnum.HR
))

RequireHoD = Depends(require_roles(
    RoleEnum.SUPER_ADMIN,
    RoleEnum.ADMIN,
    RoleEnum.HR,
    RoleEnum.HOD
))

RequireAnySevak = Depends(require_roles(
    RoleEnum.SUPER_ADMIN,
    RoleEnum.ADMIN,
    RoleEnum.HR,
    RoleEnum.HOD,
    RoleEnum.SEVAK
))