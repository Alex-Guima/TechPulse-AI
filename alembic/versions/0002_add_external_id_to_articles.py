"""add external_id to articles

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-04 00:00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "articles",
        sa.Column("external_id", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("articles", "external_id")
