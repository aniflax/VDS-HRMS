"""add half day period to leave requests

Revision ID: b4f2c8a9d1e3
Revises: 876850acf3e7
Create Date: 2026-05-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b4f2c8a9d1e3'
down_revision: Union[str, Sequence[str], None] = '876850acf3e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('leave_requests', sa.Column('half_day_period', sa.String(length=20), nullable=True))


def downgrade() -> None:
    op.drop_column('leave_requests', 'half_day_period')
