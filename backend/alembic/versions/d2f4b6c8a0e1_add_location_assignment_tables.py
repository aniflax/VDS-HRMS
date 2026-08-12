"""add location assignment tables

Revision ID: d2f4b6c8a0e1
Revises: c7d8e9f0a1b2
Create Date: 2026-05-08 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "d2f4b6c8a0e1"
down_revision: Union[str, Sequence[str], None] = "c7d8e9f0a1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())

    if not inspector.has_table("locations"):
        op.create_table(
            "locations",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("address", sa.Text(), nullable=True),
            sa.Column("latitude", sa.Float(), nullable=False),
            sa.Column("longitude", sa.Float(), nullable=False),
            sa.Column("geo_threshold_meters", sa.Integer(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("name"),
        )

    if not inspector.has_table("department_locations"):
        op.create_table(
            "department_locations",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("department_id", sa.String(length=36), nullable=False),
            sa.Column("location_id", sa.String(length=36), nullable=False),
            sa.Column("is_primary", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )

    if not inspector.has_table("sevak_locations"):
        op.create_table(
            "sevak_locations",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("sevak_id", sa.String(length=36), nullable=False),
            sa.Column("department_id", sa.String(length=36), nullable=False),
            sa.Column("location_name", sa.String(length=200), nullable=True),
            sa.Column("location_lat", sa.Float(), nullable=True),
            sa.Column("location_lng", sa.Float(), nullable=True),
            sa.Column("is_primary", sa.Boolean(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("assigned_at", sa.DateTime(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
            sa.ForeignKeyConstraint(["sevak_id"], ["sevaks.id"]),
            sa.PrimaryKeyConstraint("id"),
        )


def downgrade() -> None:
    inspector = inspect(op.get_bind())
    if inspector.has_table("sevak_locations"):
        op.drop_table("sevak_locations")
    if inspector.has_table("department_locations"):
        op.drop_table("department_locations")
    if inspector.has_table("locations"):
        op.drop_table("locations")
