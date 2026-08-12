"""Fix HODs without department.

Downgrades any HOD that has no department_id to SEVAK, since a HOD must
have a department to manage. This was a data fix for the period before the
backend service started enforcing this constraint on department deletion /
profile updates.

Revision ID: h1o2d3f4i5x6
Revises: n1o2t3i4f5y6
Create Date: 2026-07-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'h1o2t3f4i5x6'
down_revision: Union[str, Sequence[str], None] = 'n1o2t3i4f5y6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE sevaks
        SET role = 'SEVAK'
        WHERE role = 'HOD' AND department_id IS NULL
        """
    )


def downgrade() -> None:
    # Data fix only — no schema or data reversal needed.
    pass
