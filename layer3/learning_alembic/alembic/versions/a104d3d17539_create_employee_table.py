"""Create Employee Table

Revision ID: a104d3d17539
Revises: 
Create Date: 2026-03-17 12:22:13.242712

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a104d3d17539'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "employee",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("current", sa.Boolean, default=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("employee")
