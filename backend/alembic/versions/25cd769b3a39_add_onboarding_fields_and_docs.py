"""Add onboarding fields and docs

Revision ID: 25cd769b3a39
Revises: 6e10b1dd37ad
Create Date: 2026-03-10 15:24:34.568062

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '25cd769b3a39'
down_revision: Union[str, Sequence[str], None] = '6e10b1dd37ad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("sevaks")}
    if "department_id" not in columns:
        op.add_column('sevaks', sa.Column('department_id', sa.String(length=36), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("sevaks")}
    if "department_id" in columns:
        op.drop_column('sevaks', 'department_id')
