"""add sevak week off history

Revision ID: f7b8c9d0e1a2
Revises: e4a7c9b1d2f3
Create Date: 2026-05-24 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "f7b8c9d0e1a2"
down_revision = "e4a7c9b1d2f3"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "sevak_week_off_history",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("sevak_id", sa.String(length=36), nullable=False),
        sa.Column("week_off_day", sa.String(length=20), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["sevak_id"], ["sevaks.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sevak_week_off_history_sevak_effective", "sevak_week_off_history", ["sevak_id", "effective_from"])


def downgrade():
    op.drop_index("ix_sevak_week_off_history_sevak_effective", table_name="sevak_week_off_history")
    op.drop_table("sevak_week_off_history")
