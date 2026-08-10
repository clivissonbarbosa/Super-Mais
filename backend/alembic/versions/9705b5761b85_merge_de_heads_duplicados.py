"""merge de heads duplicados

Revision ID: 9705b5761b85
Revises: 88007349700a, f2b7d9c1a410
Create Date: 2026-08-10 19:02:32.211757

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9705b5761b85'
down_revision: Union[str, Sequence[str], None] = ('88007349700a', 'f2b7d9c1a410')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
