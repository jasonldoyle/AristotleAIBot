"""add soul_doc and ideas tables

Revision ID: 002
Revises: 001
Create Date: 2026-02-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "soul_doc",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "ideas",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("idea", sa.Text(), nullable=False),
        sa.Column("context", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="parked"),
        sa.Column("parked_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("eligible_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("ideas")
    op.drop_table("soul_doc")
