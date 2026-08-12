"""Backfill all existing timestamps from UTC to IST.

All DateTime columns were originally stored using datetime.utcnow() (UTC).
The codebase has been switched to store IST via get_local_now(). This
migration adds +5 hours 30 minutes to every non-null DateTime value so
the existing rows match the new IST convention.

Guarded by a system_config flag so it runs at most once.

Revision ID: z1_backfill_ist
Revises: h1o2t3f4i5x6
Create Date: 2026-07-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'z1_backfill_ist'
down_revision: Union[str, Sequence[str], None] = 'h1o2t3f4i5x6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INTERVAL = "5 hours 30 minutes"

# (table, column) pairs to shift
COLUMNS: list[tuple[str, str]] = [
    ("sevaks", "created_at"),
    ("sevaks", "updated_at"),
    ("sevaks", "activated_at"),
    ("sevaks", "last_login"),
    ("sevaks", "password_reset_token_issued_at"),
    ("account_events", "timestamp"),
    ("account_events", "resolved_at"),
    ("attendance_logs", "created_at"),
    ("attendance_logs", "updated_at"),
    ("attendance_logs", "check_in_time"),
    ("attendance_logs", "check_out_time"),
    ("locations", "created_at"),
    ("locations", "updated_at"),
    ("departments", "created_at"),
    ("departments", "updated_at"),
    ("department_locations", "created_at"),
    ("department_locations", "updated_at"),
    ("leave_types", "created_at"),
    ("leave_types", "updated_at"),
    ("leave_balances", "created_at"),
    ("leave_balances", "updated_at"),
    ("leave_requests", "created_at"),
    ("leave_requests", "updated_at"),
    ("leave_requests", "last_notified_at"),
    ("sevak_locations", "created_at"),
    ("sevak_locations", "updated_at"),
    ("sevak_locations", "assigned_at"),
    ("sevak_week_off_history", "created_at"),
    ("audit_logs", "timestamp"),
    ("system_config", "modified_at"),
]


def _already_run(conn: sa.Connection) -> bool:
    row = conn.execute(
        sa.text(
            "SELECT 1 FROM system_config WHERE key = 'timestamps_backfilled_to_ist' LIMIT 1"
        )
    ).fetchone()
    return row is not None


def _set_flag(conn: sa.Connection) -> None:
    conn.execute(
        sa.text(
            "INSERT INTO system_config (id, key, value, access_level, modified_at) "
            "VALUES (gen_random_uuid()::text, 'timestamps_backfilled_to_ist', 'true', 'SUPER_ADMIN', NOW()) "
            "ON CONFLICT (key) DO UPDATE SET value = 'true', modified_at = NOW()"
        )
    )


def upgrade() -> None:
    conn = op.get_bind()
    if _already_run(conn):
        return

    for table, column in COLUMNS:
        op.execute(
            sa.text(
                f'UPDATE {table} SET {column} = {column} + INTERVAL \'{INTERVAL}\' '
                f'WHERE {column} IS NOT NULL'
            )
        )

    _set_flag(conn)


def downgrade() -> None:
    conn = op.get_bind()
    if not _already_run(conn):
        return

    for table, column in COLUMNS:
        op.execute(
            sa.text(
                f'UPDATE {table} SET {column} = {column} - INTERVAL \'{INTERVAL}\' '
                f'WHERE {column} IS NOT NULL'
            )
        )

    conn.execute(
        sa.text("DELETE FROM system_config WHERE key = 'timestamps_backfilled_to_ist'")
    )
