"""Create Model Table

Revision ID: abb6342059f5
Revises: 
Create Date: 2026-03-16 23:40:22.333956

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'abb6342059f5'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "model",
        sa.Column("")
    )

def downgrade() -> None:
    """Downgrade schema."""
    pass
