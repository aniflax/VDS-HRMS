"""add missing sevak profile columns

Revision ID: e4a7c9b1d2f3
Revises: d2f4b6c8a0e1
Create Date: 2026-05-08 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "e4a7c9b1d2f3"
down_revision: Union[str, Sequence[str], None] = "d2f4b6c8a0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _columns(table_name: str) -> set[str]:
    return {column["name"] for column in inspect(op.get_bind()).get_columns(table_name)}


def upgrade() -> None:
    columns = _columns("sevaks")
    missing_columns = [
        ("phone", sa.Column("phone", sa.String(length=20), nullable=True)),
        ("address", sa.Column("address", sa.Text(), nullable=True)),
        ("id_proof_path", sa.Column("id_proof_path", sa.String(length=500), nullable=True)),
        ("pan_card_path", sa.Column("pan_card_path", sa.String(length=500), nullable=True)),
        ("passbook_path", sa.Column("passbook_path", sa.String(length=500), nullable=True)),
    ]

    for column_name, column in missing_columns:
        if column_name not in columns:
            op.add_column("sevaks", column)


def downgrade() -> None:
    columns = _columns("sevaks")
    for column_name in ["passbook_path", "pan_card_path", "id_proof_path", "address", "phone"]:
        if column_name in columns:
            op.drop_column("sevaks", column_name)
