"""add email verification and reset validity config

Revision ID: 9a7c8e1f4b2d
Revises: 21b8738acdcb, 73d5f20ab1c2
Create Date: 2026-04-21 12:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '9a7c8e1f4b2d'
down_revision: Union[str, Sequence[str], None] = ('21b8738acdcb', '73d5f20ab1c2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'sevaks',
        sa.Column('email_verified', sa.Boolean(), nullable=False, server_default=sa.text('false'))
    )
    op.execute("UPDATE sevaks SET email_verified = true WHERE email IS NOT NULL")


def downgrade() -> None:
    op.drop_column('sevaks', 'email_verified')
