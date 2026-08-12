"""add is_manual to attendance

Revision ID: 73d5f20ab1c2
Revises: 62c4e10fa5b3
Create Date: 2026-03-28 12:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '73d5f20ab1c2'
down_revision: Union[str, Sequence[str], None] = '62c4e10fa5b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('attendance_logs', sa.Column('is_manual', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('attendance_logs', sa.Column('unlocked_by_id', sa.String(36), nullable=True))


def downgrade() -> None:
    op.drop_column('attendance_logs', 'is_manual')
    op.drop_column('attendance_logs', 'unlocked_by_id')
