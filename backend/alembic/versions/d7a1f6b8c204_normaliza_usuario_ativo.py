"""normaliza usuario ativo

Revision ID: d7a1f6b8c204
Revises: c1e8a4d2f930
Create Date: 2026-08-10
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "d7a1f6b8c204"
down_revision: str | None = "c1e8a4d2f930"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("UPDATE usuario SET ativo = true WHERE ativo IS NULL")
    op.alter_column(
        "usuario",
        "ativo",
        existing_type=sa.Boolean(),
        nullable=False,
        server_default=sa.true(),
    )


def downgrade() -> None:
    op.alter_column(
        "usuario",
        "ativo",
        existing_type=sa.Boolean(),
        nullable=True,
        server_default=None,
    )
