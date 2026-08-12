from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import Response
from datetime import datetime
from typing import List, Optional
from app.core.config import settings
from app.core.dependencies import DbSession, CurrentSevak
from app.services.attendance import get_local_now
from app.schemas.sevak import (
    AccountCredentialsEmailRequest,
    AdminAccountCreate,
    AdminAccountCreateResponse,
    AdminAccountOtpRequest,
    AdminAccountOtpResponse,
    AdminAccountOtpVerifyRequest,
    AdminAccountOtpVerifyResponse,
    DeleteRequestResponse,
    SevakCreate,
    SevakUpdate,
    SevakAdminUpdate,
    SevakResponse,
    LockedAccountResponse,
)

from app.services.sevak import (
    create_sevak,
    create_privileged_account,
    get_all_sevaks,
    get_onboarding_sevaks,
    get_sevak_by_id,
    request_admin_account_email_otp,
    update_sevak_profile,
    admin_update_sevak,
    verify_admin_account_email_otp,
)
from app.models.sevak import RoleEnum, Sevak as SevakModel, AccountEvent, SevakStatusEnum
from app.models.attendance import AttendanceLog
from app.models.leave import LeaveBalance, LeaveRequest
from app.models.sevak_location import SevakLocation
from app.models.audit import AuditLog
from app.services.notifications import create_password_reset_notification, send_account_credentials_email
from app.services.auth import resend_activation_email
from app.services.storage import get_document, save_document_upload
from app.services.week_off_history import serialize_week_off_history
from sqlalchemy import desc


router = APIRouter(prefix="/api/sevaks", tags=["Sevak Management"])


def serialize_sevak_response(db, sevak):
    data = {**sevak.__dict__}
    data["week_off_history"] = serialize_week_off_history(db, sevak)
    return data


@router.post("/", response_model=SevakResponse, status_code=status.HTTP_201_CREATED)
def create_new_sevak(
    sevak_in: SevakCreate,
    current_user: CurrentSevak,
    db: DbSession
):
    """Create a new Sevak (Admin/HR only)."""
    if current_user.role not in [RoleEnum.HR, RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to create a Sevak"
        )
    return create_sevak(db=db, sevak_in=sevak_in, created_by=current_user)


@router.get("/", response_model=List[SevakResponse])
def get_sevaks(
    current_user: CurrentSevak,
    db: DbSession,
    skip: int = 0,
    limit: int = 100,
    department_id: Optional[str] = None
):
    """List all Sevaks based on Role visibility rules."""
    return get_all_sevaks(
        db=db,
        current_user=current_user,
        skip=skip,
        limit=limit,
        department_id=department_id
    )


# ─── Admin GET routes MUST be above /{sevak_id} to avoid being shadowed ─────────

@router.get("/admin/accounts", response_model=List[SevakResponse])
def get_all_accounts(db: DbSession, current_user: CurrentSevak):
    """Admin/SuperAdmin: Get ALL accounts (any status) for management."""
    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorised.")
    return db.query(SevakModel).order_by(SevakModel.sevak_id).all()


@router.post("/admin/accounts", response_model=AdminAccountCreateResponse, status_code=status.HTTP_201_CREATED)
def create_admin_or_hr_account(
    payload: AdminAccountCreate,
    db: DbSession,
    current_user: CurrentSevak,
):
    """SuperAdmin: Create reserved Admin/HR accounts."""
    account, temporary_password, invitation_sent = create_privileged_account(
        db=db,
        account_in=payload,
        created_by=current_user,
    )
    return {
        "account": account,
        "temporary_password": temporary_password,
        "invitation_sent": invitation_sent,
        "message": (
            f"{account.role.value.replace('_', ' ')} account {account.sevak_id} created. "
            "Share the one-time password securely and ask the recipient to activate their account."
        ),
    }


@router.post("/admin/accounts/otp/send", response_model=AdminAccountOtpResponse)
def send_admin_or_hr_account_otp(
    payload: AdminAccountOtpRequest,
    db: DbSession,
    current_user: CurrentSevak,
):
    """SuperAdmin: Send OTP before Admin/HR account information is accepted."""
    email, otp_token, sent = request_admin_account_email_otp(
        db=db,
        email=payload.email,
        requested_by=current_user,
    )
    environment = settings.ENVIRONMENT.lower()
    if not sent and environment not in {"development", "test"}:
        raise HTTPException(status_code=500, detail="Failed to send OTP email.")
    return {
        "email": email,
        "otp_token": otp_token,
        "message": f"OTP sent to {email}.",
    }


@router.post("/admin/accounts/otp/verify", response_model=AdminAccountOtpVerifyResponse)
def verify_admin_or_hr_account_otp(
    payload: AdminAccountOtpVerifyRequest,
    current_user: CurrentSevak,
):
    """SuperAdmin: Verify OTP and issue a short-lived account creation token."""
    if current_user.role != RoleEnum.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Only SuperAdmin can verify account OTP.")
    email, verification_token = verify_admin_account_email_otp(
        email=payload.email,
        otp=payload.otp,
        otp_token=payload.otp_token,
    )
    return {
        "email": email,
        "email_verification_token": verification_token,
        "message": "Email verified. Enter account information to continue.",
    }


@router.post("/admin/accounts/{sevak_id}/send-credentials")
def send_admin_or_hr_credentials(
    sevak_id: str,
    payload: AccountCredentialsEmailRequest,
    db: DbSession,
    current_user: CurrentSevak,
):
    """SuperAdmin: Send the generated account ID and temporary password."""
    if current_user.role != RoleEnum.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Only SuperAdmin can send account credentials.")

    account = get_sevak_by_id(db, sevak_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found.")
    if account.role not in [RoleEnum.ADMIN, RoleEnum.HR]:
        raise HTTPException(status_code=400, detail="Credentials can be sent only for Admin or HR accounts.")
    if not account.email:
        raise HTTPException(status_code=400, detail="Account does not have an email address configured.")

    login_link = f"{settings.FRONTEND_URL.rstrip('/')}/login"
    sent = send_account_credentials_email(
        db=db,
        sevak=account,
        temporary_password=payload.temporary_password,
        login_link=login_link,
        requested_by_name=f"{current_user.first_name} {current_user.last_name}",
    )
    if not sent:
        raise HTTPException(status_code=500, detail="Failed to send login details email.")
    return {"message": f"Login details sent to {account.email}."}


@router.get("/admin/delete-requests", response_model=List[DeleteRequestResponse])
def get_delete_requests(db: DbSession, current_user: CurrentSevak):
    """Admin/SuperAdmin: Get accounts with pending delete request, with requester name resolved."""
    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorised.")
    results = []
    for sevak in db.query(SevakModel).filter(SevakModel.delete_requested == True).all():
        requester_name = None
        if sevak.delete_requested_by:
            requester = db.query(SevakModel).filter(SevakModel.id == sevak.delete_requested_by).first()
            if requester:
                requester_name = f"{requester.first_name} {requester.last_name}"
        results.append(DeleteRequestResponse(
            id=sevak.id,
            sevak_id=sevak.sevak_id,
            first_name=sevak.first_name,
            last_name=sevak.last_name,
            email=sevak.email,
            role=sevak.role,
            delete_requested_by=sevak.delete_requested_by,
            delete_requested_by_name=requester_name or "Unknown",
        ))
    return results


@router.get("/onboarding", response_model=List[SevakResponse])
def get_sevaks_onboarding(
    db: DbSession,
    current_user: CurrentSevak,
    month: Optional[int] = None,
    year: Optional[int] = None,
    cutoff: Optional[int] = None,
):
    """HR/Admin/SuperAdmin: Get all self-onboarded sevaks (both activated and pending).
    Filter by financial month using month+year+cutoff params.
    Financial month: (cutoff+1) of prev calendar month to cutoff of current calendar month.
    E.g. month=4, year=2026, cutoff=20 => 21 Mar 2026 to 20 Apr 2026.
    """
    start_date = None
    end_date = None
    if month is not None and year is not None:
        # Resolve cutoff from DB if not provided by client
        if cutoff is None:
            from app.models.department import SystemConfig
            cfg = db.query(SystemConfig).filter(SystemConfig.key == "FINANCIAL_CUTOFF_DATE").first()
            cutoff = int(cfg.value) if cfg and cfg.value else 20
        cutoff = max(1, min(cutoff, 27))  # guard: clamp between 1 and 27
        prev_month = 12 if month == 1 else month - 1
        prev_year = year - 1 if month == 1 else year
        start_date = datetime(prev_year, prev_month, cutoff + 1, 0, 0, 0)
        end_date = datetime(year, month, cutoff, 23, 59, 59)
    return get_onboarding_sevaks(db=db, current_user=current_user, start_date=start_date, end_date=end_date)


@router.get("/admin/locked-list", response_model=List[LockedAccountResponse])
def get_locked_accounts(db: DbSession, current_user: CurrentSevak):
    """Admin/SuperAdmin: Get list of locked accounts with reasons."""
    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorised.")

    locked_sevaks = db.query(SevakModel).filter(SevakModel.status == SevakStatusEnum.LOCKED).all()
    results = []
    for s in locked_sevaks:
        # Get the latest LOCK event for this user
        last_event = db.query(AccountEvent).filter(
            AccountEvent.sevak_id == s.id,
            AccountEvent.event_type == "LOCKED"
        ).order_by(desc(AccountEvent.timestamp)).first()

        results.append({
            "id": s.id,
            "sevak_id": s.sevak_id,
            "first_name": s.first_name,
            "last_name": s.last_name,
            "email": s.email,
            "email_verified": s.email_verified,
            "phone": s.phone,
            "lock_reason": last_event.notes if last_event else "Account locked out (Admin review required)",
            "locked_at": last_event.timestamp if last_event else s.updated_at,
            "reset_pending": False
        })
    return results


@router.delete("/admin/system/clean", status_code=status.HTTP_204_NO_CONTENT)
def system_data_cleanup(
    db: DbSession,
    current_user: CurrentSevak
):
    """SUPER ADMIN ONLY - Wipes non-admin app data as requested."""
    if current_user.role != RoleEnum.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Only SUPER_ADMIN can perform data resets.")

    from app.models.attendance import AttendanceLog
    from app.models.leave import LeaveRequest, LeaveBalance, LeaveType
    from app.models.department import Department
    from app.models.sevak import Sevak, AccountEvent
    from app.models.sevak_location import SevakLocation
    from app.models.week_off_history import SevakWeekOffHistory

    try:
        db.query(AccountEvent).delete()
        db.query(SevakLocation).delete()
        db.query(SevakWeekOffHistory).delete()
        db.query(AttendanceLog).delete()
        db.query(LeaveRequest).delete()
        db.query(LeaveBalance).delete()
        db.query(Sevak).update({"department_id": None}, synchronize_session=False)
        db.query(Department).update({"hod_id": None}, synchronize_session=False)
        db.commit()
        db.query(Department).delete()
        db.query(Sevak).filter(Sevak.role != RoleEnum.SUPER_ADMIN).delete()
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to reset data: {str(e)}")


# ─── Dynamic /{sevak_id} routes MUST come after all /admin/* routes ──────────

@router.get("/{sevak_id}", response_model=SevakResponse)
def get_sevak(
    sevak_id: str,
    current_user: CurrentSevak,
    db: DbSession
):
    """Get a specific Sevak."""
    sevak = get_sevak_by_id(db=db, id=sevak_id)
    if not sevak:
        raise HTTPException(status_code=404, detail="Sevak not found")

    # Visibility checks
    if current_user.role == RoleEnum.SEVAK and current_user.id != sevak_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this profile")
    if current_user.role == RoleEnum.HOD and current_user.department_id != sevak.department_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this profile")

    return serialize_sevak_response(db, sevak)


@router.put("/{sevak_id}", response_model=SevakResponse)
def update_sevak(
    sevak_id: str,
    sevak_in: SevakUpdate,
    current_user: CurrentSevak,
    db: DbSession
):
    """Update profile logic. Users can update their own general info."""
    db_sevak = get_sevak_by_id(db=db, id=sevak_id)
    if not db_sevak:
        raise HTTPException(status_code=404, detail="Sevak not found")

    # Standard profile edit restriction
    if current_user.role == RoleEnum.SEVAK and current_user.id != db_sevak.id:
        raise HTTPException(status_code=403, detail="Cannot update other users")

    updated = update_sevak_profile(db=db, db_sevak=db_sevak, sevak_in=sevak_in)
    return serialize_sevak_response(db, updated)


@router.put("/{sevak_id}/admin", response_model=SevakResponse)
def admin_update(
    sevak_id: str,
    sevak_in: SevakAdminUpdate,
    current_user: CurrentSevak,
    db: DbSession
):
    """Admin updates for strict fields like role and status."""
    db_sevak = get_sevak_by_id(db=db, id=sevak_id)
    if not db_sevak:
        raise HTTPException(status_code=404, detail="Sevak not found")

    updated = admin_update_sevak(db=db, db_sevak=db_sevak, sevak_in=sevak_in, current_user=current_user)
    return serialize_sevak_response(db, updated)


@router.post("/{sevak_id}/documents", response_model=SevakResponse)
async def upload_document(
    sevak_id: str,
    db: DbSession,
    current_user: CurrentSevak,
    doc_type: str = Form(...),
    file: UploadFile = File(...)
):
    """Upload or update a single document for a Sevak (HR only)."""
    if current_user.role not in [RoleEnum.HR, RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Only HR/Admin can modify documents.")

    db_sevak = get_sevak_by_id(db=db, id=sevak_id)
    if not db_sevak:
        raise HTTPException(status_code=404, detail="Sevak not found")

    if doc_type not in ['id_proof', 'pan_card', 'passbook']:
        raise HTTPException(status_code=400, detail="Invalid document type")

    stored = await save_document_upload(file, sevak_id=db_sevak.id, doc_type=doc_type)

    if doc_type == 'id_proof':
        db_sevak.id_proof_path = stored.key
    elif doc_type == 'pan_card':
        db_sevak.pan_card_path = stored.key
    elif doc_type == 'passbook':
        db_sevak.passbook_path = stored.key

    db.commit()
    db.refresh(db_sevak)
    return db_sevak


@router.get("/{sevak_id}/documents/{doc_type}")
def download_document(
    sevak_id: str,
    doc_type: str,
    db: DbSession,
    current_user: CurrentSevak,
):
    """Serve private Sevak documents through authenticated API access."""
    db_sevak = get_sevak_by_id(db=db, id=sevak_id)
    if not db_sevak:
        raise HTTPException(status_code=404, detail="Sevak not found")

    if current_user.role == RoleEnum.SEVAK and current_user.id != db_sevak.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this document")
    if current_user.role == RoleEnum.HOD and current_user.department_id != db_sevak.department_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this document")
    if current_user.role not in [RoleEnum.SEVAK, RoleEnum.HOD, RoleEnum.HR, RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized to view this document")

    document_key = {
        "id_proof": db_sevak.id_proof_path,
        "pan_card": db_sevak.pan_card_path,
        "passbook": db_sevak.passbook_path,
    }.get(doc_type)
    if not document_key:
        raise HTTPException(status_code=404, detail="Document not found")

    document = get_document(document_key)
    return Response(
        content=document.body,
        media_type=document.content_type,
        headers={
            "Content-Disposition": f'inline; filename="{document.filename}"',
            "Cache-Control": "private, max-age=300",
        },
    )


# ─── Account Management (POST routes for /{sevak_id}) ───────────────────────────


@router.post("/{sevak_id}/unlock")
def unlock_account(sevak_id: str, db: DbSession, current_user: CurrentSevak):
    """Admin/SuperAdmin: Unlock a locked account."""
    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorised.")
    sevak = get_sevak_by_id(db, sevak_id)
    if not sevak:
        raise HTTPException(status_code=404, detail="Sevak not found.")
    sevak.status = SevakStatusEnum.ACTIVE
    sevak.failed_login_attempts = 0
    event = AccountEvent(
        sevak_id=sevak.id,
        event_type="UNLOCKED",
        resolved_by=current_user.id,
        resolved_at=get_local_now()
    )
    db.add(event)
    db.commit()
    return {"message": f"Account {sevak.sevak_id} unlocked successfully."}


@router.post("/{sevak_id}/lock")
def lock_account(sevak_id: str, db: DbSession, current_user: CurrentSevak):
    """Admin/SuperAdmin: Lock an account manually."""
    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorised.")
    sevak = get_sevak_by_id(db, sevak_id)
    if not sevak:
        raise HTTPException(status_code=404, detail="Sevak not found.")

    if sevak.role == RoleEnum.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Super Admin accounts cannot be locked.")

    sevak.status = SevakStatusEnum.LOCKED
    event = AccountEvent(
        sevak_id=sevak.id,
        event_type="LOCKED",
        resolved_by=current_user.id,
        notes="Account locked manually by Admin"
    )
    db.add(event)
    db.commit()

    return {"message": f"Account {sevak.sevak_id} locked successfully."}


@router.post("/{sevak_id}/activate")
def activate_account(sevak_id: str, db: DbSession, current_user: CurrentSevak):
    """Admin/HR: Activate a deactivated account. Auto-clears any pending delete request."""
    if current_user.role not in [RoleEnum.HR, RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorised.")
    sevak = get_sevak_by_id(db, sevak_id)
    if not sevak:
        raise HTTPException(status_code=404, detail="Sevak not found.")
    sevak.status = SevakStatusEnum.ACTIVE
    sevak.activated_at = get_local_now()
    sevak.delete_requested = False
    sevak.delete_requested_by = None
    event = AccountEvent(
        sevak_id=sevak.id,
        event_type="ACTIVATED",
        resolved_by=current_user.id,
        notes="Account activated from HR/Admin directory"
    )
    db.add(event)
    db.commit()
    return {"message": f"Account {sevak.sevak_id} activated successfully."}


@router.post("/{sevak_id}/resend-activation-email")
def resend_activation_email_endpoint(sevak_id: str, db: DbSession, current_user: CurrentSevak):
    """Resend account activation email to a sevak."""
    sevak = get_sevak_by_id(db, sevak_id)
    if not sevak:
        raise HTTPException(status_code=404, detail="Sevak not found.")

    if current_user.role == RoleEnum.SEVAK and current_user.id != sevak_id:
        raise HTTPException(status_code=403, detail="Not authorised.")

    if current_user.role not in [RoleEnum.SEVAK, RoleEnum.HOD, RoleEnum.HR, RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorised.")

    sent = resend_activation_email(
        db=db,
        sevak=sevak,
        requested_by_name=f"{current_user.first_name} {current_user.last_name}"
    )
    if not sent:
        raise HTTPException(status_code=500, detail="Failed to send activation email.")
    return {"message": f"Activation email sent to {sevak.email} successfully."}


@router.post("/{sevak_id}/reset-password-notify")
def reset_password_notify(sevak_id: str, db: DbSession, current_user: CurrentSevak):
    """Admin/SuperAdmin: Trigger password reset notification with email link."""
    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorised.")
    sevak = get_sevak_by_id(db, sevak_id)
    if not sevak:
        raise HTTPException(status_code=404, detail="Sevak not found.")

    if not sevak.email:
        raise HTTPException(status_code=400, detail="Sevak does not have an email address configured.")

    sent = create_password_reset_notification(
        db=db,
        sevak=sevak,
        requested_by_id=current_user.id,
        requested_by_name=f"{current_user.first_name} {current_user.last_name}",
        notes=f"Reset link requested by {current_user.first_name} {current_user.last_name}",
    )

    if not sent:
        raise HTTPException(status_code=500, detail="Failed to send reset email.")

    return {"message": f"Password reset link sent to {sevak.email} successfully."}


@router.post("/{sevak_id}/delete-request")
def request_deletion(sevak_id: str, db: DbSession, current_user: CurrentSevak):
    """HR: Flag an inactive account for deletion review by Admin/SuperAdmin."""
    if current_user.role not in [RoleEnum.HR, RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorised.")
    sevak = get_sevak_by_id(db, sevak_id)
    if not sevak:
        raise HTTPException(status_code=404, detail="Sevak not found.")
    if sevak.status != SevakStatusEnum.INACTIVE:
        raise HTTPException(status_code=400, detail="Only INACTIVE accounts can be flagged for deletion.")
    sevak.delete_requested = True
    sevak.delete_requested_by = current_user.id
    db.commit()
    return {"message": "Deletion request submitted. Admin will review."}


@router.delete("/{sevak_id}/delete-request")
def withdraw_delete_request(sevak_id: str, db: DbSession, current_user: CurrentSevak):
    """HR/Admin: Withdraw a pending delete request."""
    if current_user.role not in [RoleEnum.HR, RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorised.")
    sevak = get_sevak_by_id(db, sevak_id)
    if not sevak:
        raise HTTPException(status_code=404, detail="Sevak not found.")
    if not sevak.delete_requested:
        raise HTTPException(status_code=400, detail="No pending delete request for this account.")
    sevak.delete_requested = False
    sevak.delete_requested_by = None
    db.commit()
    return {"message": "Delete request withdrawn."}


@router.delete("/{sevak_id}/hard-delete")
def hard_delete_account(sevak_id: str, db: DbSession, current_user: CurrentSevak):
    """SuperAdmin: Permanently delete account. Admin can delete if delete_requested=True."""
    sevak = get_sevak_by_id(db, sevak_id)
    if not sevak:
        raise HTTPException(status_code=404, detail="Sevak not found.")
    if sevak.role == RoleEnum.SUPER_ADMIN:
        raise HTTPException(status_code=400, detail="Cannot delete SuperAdmin account.")

    if current_user.role == RoleEnum.ADMIN and not sevak.delete_requested:
        raise HTTPException(status_code=403, detail="Account has no pending delete request. Request deletion first.")
    if current_user.role not in [RoleEnum.SUPER_ADMIN, RoleEnum.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorised.")

    # Remove or detach records that reference this Sevak so FK constraints don't block deletion.
    db.query(AttendanceLog).filter(AttendanceLog.sevak_id == sevak.id).delete(synchronize_session=False)
    db.query(AttendanceLog).filter(AttendanceLog.unlocked_by_id == sevak.id).update(
        {AttendanceLog.unlocked_by_id: None},
        synchronize_session=False
    )
    db.query(LeaveBalance).filter(LeaveBalance.sevak_id == sevak.id).delete(synchronize_session=False)
    db.query(LeaveRequest).filter(LeaveRequest.sevak_id == sevak.id).delete(synchronize_session=False)
    db.query(LeaveRequest).filter(LeaveRequest.approver_hod_id == sevak.id).update(
        {LeaveRequest.approver_hod_id: None},
        synchronize_session=False
    )
    db.query(LeaveRequest).filter(LeaveRequest.approver_hr_id == sevak.id).update(
        {LeaveRequest.approver_hr_id: None},
        synchronize_session=False
    )
    db.query(SevakLocation).filter(SevakLocation.sevak_id == sevak.id).delete(synchronize_session=False)
    db.query(AccountEvent).filter(AccountEvent.sevak_id == sevak.id).delete(synchronize_session=False)
    db.query(AuditLog).filter(AuditLog.performed_by == sevak.id).delete(synchronize_session=False)

    if current_user.role in [RoleEnum.SUPER_ADMIN, RoleEnum.ADMIN]:
        db.delete(sevak)
        db.commit()
        return {"message": "Account permanently deleted."}
    else:
        raise HTTPException(status_code=403, detail="Not authorised.")
