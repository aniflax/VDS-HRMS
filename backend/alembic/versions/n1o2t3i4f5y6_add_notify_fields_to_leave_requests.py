"""add notify fields to leave requests

Adds last_notified_at (nullable timestamp) and notify_count (int, default 0)
to the leave_requests table so the new /api/leave/notify/{id} endpoint can
record reminder history and enforce the 24h cooldown per request.

Revision ID: n1o2t3i4f5y6
Revises: f7b8c9d0e1a2
Create Date: 2026-07-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'n1o2t3i4f5y6'
down_revision: Union[str, Sequence[str], None] = 'f7b8c9d0e1a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'leave_requests',
        sa.Column('last_notified_at', sa.DateTime(), nullable=True),
    )
    op.add_column(
        'leave_requests',
        sa.Column(
            'notify_count',
            sa.Integer(),
            nullable=False,
            server_default='0',
        ),
    )


def downgrade() -> None:
    op.drop_column('leave_requests', 'notify_count')
    op.drop_column('leave_requests', 'last_notified_at')
