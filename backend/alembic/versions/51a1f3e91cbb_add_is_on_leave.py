"""add is_on_leave

Revision ID: 51a1f3e91cbb
Revises: 21b8738acdcb
Create Date: 2026-03-26 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '51a1f3e91cbb'
down_revision: Union[str, Sequence[str], None] = '21b8738acdcb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('sevaks', sa.Column('is_on_leave', sa.Boolean(), server_default='0', nullable=False))


def downgrade() -> None:
    op.drop_column('sevaks', 'is_on_leave')
