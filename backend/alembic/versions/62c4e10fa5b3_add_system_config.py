"""add system_config

Revision ID: 62c4e10fa5b3
Revises: 51a1f3e91cbb
Create Date: 2026-03-26 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = '62c4e10fa5b3'
down_revision: Union[str, Sequence[str], None] = '51a1f3e91cbb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if not inspect(op.get_bind()).has_table('system_config'):
        op.create_table('system_config',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('key', sa.String(100), unique=True, nullable=False),
            sa.Column('value', sa.Text(), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('access_level', sa.Enum('SUPER_ADMIN', 'ADMIN', 'HR', name='configaccesslevel'), nullable=False),
            sa.Column('modified_by', sa.String(36), nullable=True),
            sa.Column('modified_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )

    op.execute("""
        INSERT INTO system_config (id, key, value, description, access_level, modified_at)
        VALUES ('geo_default', 'GEO_THRESHOLD_METERS', '50', 'Geo validation threshold in meters', 'HR', NOW())
        ON CONFLICT (key) DO NOTHING
    """)
    op.execute("""
        INSERT INTO system_config (id, key, value, description, access_level, modified_at)
        VALUES ('leave_sla', 'LEAVE_APPROVAL_SLA_DAYS', '2', 'Days for leave approver to act', 'HR', NOW())
        ON CONFLICT (key) DO NOTHING
    """)


def downgrade() -> None:
    if inspect(op.get_bind()).has_table('system_config'):
        op.drop_table('system_config')
