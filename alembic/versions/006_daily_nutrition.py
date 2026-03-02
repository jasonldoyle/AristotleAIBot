"""Replace nutrition_logs (monthly) with daily_nutrition (daily MFP entries)

Revision ID: 006
Revises: 005
Create Date: 2026-03-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("nutrition_logs")

    op.create_table(
        "daily_nutrition",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("date", sa.String(), nullable=False, unique=True),
        sa.Column("calories", sa.Integer(), nullable=False),
        sa.Column("protein_g", sa.Integer(), nullable=False),
        sa.Column("carbs_g", sa.Integer(), nullable=False),
        sa.Column("fat_g", sa.Integer(), nullable=False),
        sa.Column("block_id", UUID(as_uuid=True), sa.ForeignKey("training_blocks.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("daily_nutrition")

    op.create_table(
        "nutrition_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("month", sa.String(), nullable=False, unique=True),
        sa.Column("avg_calories", sa.Integer(), nullable=True),
        sa.Column("avg_protein_g", sa.Integer(), nullable=True),
        sa.Column("avg_carbs_g", sa.Integer(), nullable=True),
        sa.Column("avg_fat_g", sa.Integer(), nullable=True),
        sa.Column("block_id", UUID(as_uuid=True), sa.ForeignKey("training_blocks.id"), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
