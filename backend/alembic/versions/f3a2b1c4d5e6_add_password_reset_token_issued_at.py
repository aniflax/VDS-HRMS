"""add_password_reset_token_issued_at

Revision ID: f3a2b1c4d5e6
Revises: 9a7c8e1f4b2d
Create Date: 2026-04-28 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f3a2b1c4d5e6'
down_revision: Union[str, Sequence[str], None] = '9a7c8e1f4b2d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'sevaks',
        sa.Column('password_reset_token_issued_at', sa.DateTime(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('sevaks', 'password_reset_token_issued_at')
