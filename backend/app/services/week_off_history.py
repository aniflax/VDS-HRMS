from datetime import date, timedelta

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.models.attendance import AttendanceLog, AttendanceStatus
from app.models.leave import LeaveRequest, LeaveRequestStatus, LeaveType
from app.models.sevak import Sevak
from app.models.week_off_history import SevakWeekOffHistory


DAY_NAME_TO_NUM = {"Sunday": 0, "Monday": 1, "Tuesday": 2, "Wednesday": 3, "Thursday": 4, "Friday": 5, "Saturday": 6}
WEEK_OFF_TYPE_NAME = "Week Off"
WEEK_OFF_HISTORY_TABLE = "sevak_week_off_history"


def _history_table_exists(db: Session) -> bool:
    try:
        return inspect(db.get_bind()).has_table(WEEK_OFF_HISTORY_TABLE)
    except Exception:
        db.rollback()
        return False


def week_sunday(day: date) -> date:
    return day - timedelta(days=(day.weekday() + 1) % 7)


def week_off_date_for_week(anchor_date: date, week_off_day: str | None) -> date:
    return week_sunday(anchor_date) + timedelta(days=DAY_NAME_TO_NUM.get(week_off_day or "Sunday", 0))


def get_week_off_history(db: Session, sevak_id: str) -> list[SevakWeekOffHistory]:
    if not _history_table_exists(db):
        return []
    return db.query(SevakWeekOffHistory).filter(
        SevakWeekOffHistory.sevak_id == sevak_id
    ).order_by(SevakWeekOffHistory.effective_from.asc()).all()


def serialize_week_off_history(db: Session, sevak: Sevak) -> list[dict]:
    history = get_week_off_history(db, sevak.id)
    if not history:
        effective_from = (sevak.activated_at or sevak.created_at).date() if (sevak.activated_at or sevak.created_at) else date.min
        return [{"week_off_day": sevak.default_week_off or "Sunday", "effective_from": effective_from}]
    return [
        {"week_off_day": row.week_off_day, "effective_from": row.effective_from}
        for row in history
    ]


def get_effective_week_off_day(db: Session, sevak_id: str, target_date: date, fallback: str | None = "Sunday") -> str:
    if not _history_table_exists(db):
        return fallback or "Sunday"
    row = db.query(SevakWeekOffHistory).filter(
        SevakWeekOffHistory.sevak_id == sevak_id,
        SevakWeekOffHistory.effective_from <= target_date,
    ).order_by(SevakWeekOffHistory.effective_from.desc()).first()
    return row.week_off_day if row else (fallback or "Sunday")


def _current_week_off_consumed(db: Session, sevak: Sevak, today: date, current_week_off: str | None) -> bool:
    week_start = week_sunday(today)
    week_end = week_start + timedelta(days=6)
    current_week_off_date = week_off_date_for_week(today, current_week_off)

    if current_week_off_date < today:
        return True

    if db.query(AttendanceLog).filter(
        AttendanceLog.sevak_id == sevak.id,
        AttendanceLog.date >= week_start,
        AttendanceLog.date <= week_end,
        AttendanceLog.status == AttendanceStatus.WEEK_OFF,
    ).first():
        return True

    week_off_type = db.query(LeaveType).filter(LeaveType.name == WEEK_OFF_TYPE_NAME).first()
    if not week_off_type:
        return False

    return db.query(LeaveRequest).filter(
        LeaveRequest.sevak_id == sevak.id,
        LeaveRequest.leave_type_id == week_off_type.id,
        LeaveRequest.status.in_([LeaveRequestStatus.PENDING, LeaveRequestStatus.HOD_APPROVED, LeaveRequestStatus.APPROVED]),
        LeaveRequest.start_date >= week_start,
        LeaveRequest.start_date <= week_end,
    ).first() is not None


def get_week_off_change_effective_from(db: Session, sevak: Sevak, new_week_off: str, today: date) -> date:
    # Week-off changes always take effect from the next week, never mid-week.
    return week_sunday(today) + timedelta(days=7)


def apply_week_off_change(db: Session, sevak: Sevak, new_week_off: str, today: date) -> None:
    if not _history_table_exists(db):
        return
    current_week_off = get_effective_week_off_day(db, sevak.id, today, sevak.default_week_off)
    if new_week_off == current_week_off and new_week_off == (sevak.default_week_off or "Sunday"):
        return

    history = get_week_off_history(db, sevak.id)
    if not history:
        initial_from = (sevak.activated_at or sevak.created_at).date() if (sevak.activated_at or sevak.created_at) else today
        db.add(SevakWeekOffHistory(
            sevak_id=sevak.id,
            week_off_day=current_week_off or sevak.default_week_off or "Sunday",
            effective_from=initial_from,
        ))

    effective_from = get_week_off_change_effective_from(db, sevak, new_week_off, today)
    existing = db.query(SevakWeekOffHistory).filter(
        SevakWeekOffHistory.sevak_id == sevak.id,
        SevakWeekOffHistory.effective_from == effective_from,
    ).first()
    if existing:
        existing.week_off_day = new_week_off
    else:
        db.add(SevakWeekOffHistory(
            sevak_id=sevak.id,
            week_off_day=new_week_off,
            effective_from=effective_from,
        ))
