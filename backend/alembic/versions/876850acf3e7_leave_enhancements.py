"""leave_enhancements

Revision ID: 876850acf3e7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-30 14:36:49.370181

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = '876850acf3e7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _columns(table_name: str) -> set[str]:
    return {column["name"] for column in inspect(op.get_bind()).get_columns(table_name)}


def _foreign_keys(table_name: str) -> set[str]:
    return {fk["name"] for fk in inspect(op.get_bind()).get_foreign_keys(table_name) if fk["name"]}


def upgrade() -> None:
    """Upgrade schema."""
    attendance_columns = _columns('attendance_logs')
    if 'is_manual' in attendance_columns:
        op.alter_column('attendance_logs', 'is_manual',
                   existing_type=sa.BOOLEAN(),
                   nullable=False,
                   existing_server_default=sa.text('false'))
    if 'unlocked_by_id' in attendance_columns and 'fk_attendance_logs_unlocked_by_id_sevaks' not in _foreign_keys('attendance_logs'):
        op.create_foreign_key(
            'fk_attendance_logs_unlocked_by_id_sevaks',
            'attendance_logs',
            'sevaks',
            ['unlocked_by_id'],
            ['id'],
        )
    op.alter_column('leave_balances', 'total_allocated',
               existing_type=sa.INTEGER(),
               type_=sa.Float(),
               existing_nullable=False)
    op.alter_column('leave_balances', 'used',
               existing_type=sa.INTEGER(),
               type_=sa.Float(),
               existing_nullable=False)
    op.alter_column('leave_balances', 'pending',
               existing_type=sa.INTEGER(),
               type_=sa.Float(),
               existing_nullable=False)
    leave_request_columns = _columns('leave_requests')
    if 'is_half_day' not in leave_request_columns:
        op.add_column('leave_requests', sa.Column('is_half_day', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.alter_column('leave_requests', 'total_days',
               existing_type=sa.INTEGER(),
               type_=sa.Float(),
               existing_nullable=False)
    if 'hod_skipped' not in leave_request_columns:
        op.add_column('leave_requests', sa.Column('hod_skipped', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    else:
        op.alter_column('leave_requests', 'hod_skipped',
                   existing_type=sa.BOOLEAN(),
                   nullable=False,
                   existing_server_default=sa.text('false'))
    if 'hr_leave_modified' not in _columns('sevaks'):
        op.add_column('sevaks', sa.Column('hr_leave_modified', sa.Boolean(), server_default=sa.text('false'), nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    if 'hr_leave_modified' in _columns('sevaks'):
        op.drop_column('sevaks', 'hr_leave_modified')
    if 'hod_skipped' in _columns('leave_requests'):
        op.alter_column('leave_requests', 'hod_skipped',
                   existing_type=sa.BOOLEAN(),
                   nullable=True,
                   existing_server_default=sa.text('false'))
    op.alter_column('leave_requests', 'total_days',
               existing_type=sa.Float(),
               type_=sa.INTEGER(),
               existing_nullable=False)
    if 'is_half_day' in _columns('leave_requests'):
        op.drop_column('leave_requests', 'is_half_day')
    op.alter_column('leave_balances', 'pending',
               existing_type=sa.Float(),
               type_=sa.INTEGER(),
               existing_nullable=False)
    op.alter_column('leave_balances', 'used',
               existing_type=sa.Float(),
               type_=sa.INTEGER(),
               existing_nullable=False)
    op.alter_column('leave_balances', 'total_allocated',
               existing_type=sa.Float(),
               type_=sa.INTEGER(),
               existing_nullable=False)
    if 'fk_attendance_logs_unlocked_by_id_sevaks' in _foreign_keys('attendance_logs'):
        op.drop_constraint('fk_attendance_logs_unlocked_by_id_sevaks', 'attendance_logs', type_='foreignkey')
    if 'is_manual' in _columns('attendance_logs'):
        op.alter_column('attendance_logs', 'is_manual',
                   existing_type=sa.BOOLEAN(),
                   nullable=True,
                   existing_server_default=sa.text('false'))
