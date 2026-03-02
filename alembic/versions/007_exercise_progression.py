"""Add exercise_progression table for auto-progression tracking

Revision ID: 007
Revises: 006
Create Date: 2026-03-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "exercise_progression",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("exercise", sa.String(), nullable=False, unique=True),
        sa.Column("weight_kg", sa.Float(), nullable=False),
        sa.Column("current_reps", sa.Integer(), nullable=False),
        sa.Column("sessions_at_current", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("exercise_progression")
