"""add attendance unique constraint

Revision ID: c7d8e9f0a1b2
Revises: b4f2c8a9d1e3
Create Date: 2026-05-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import inspect


revision: str = "c7d8e9f0a1b2"
down_revision: Union[str, Sequence[str], None] = "b4f2c8a9d1e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    constraints = {
        constraint["name"]
        for constraint in inspect(op.get_bind()).get_unique_constraints("attendance_logs")
        if constraint["name"]
    }
    if "uq_attendance_logs_sevak_date" not in constraints:
        op.create_unique_constraint(
            "uq_attendance_logs_sevak_date",
            "attendance_logs",
            ["sevak_id", "date"],
        )


def downgrade() -> None:
    constraints = {
        constraint["name"]
        for constraint in inspect(op.get_bind()).get_unique_constraints("attendance_logs")
        if constraint["name"]
    }
    if "uq_attendance_logs_sevak_date" in constraints:
        op.drop_constraint(
            "uq_attendance_logs_sevak_date",
            "attendance_logs",
            type_="unique",
        )
