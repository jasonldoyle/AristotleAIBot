"""add fitness tables: training_blocks, workout_sessions, exercise_logs,
workout_modifications, weigh_ins, nutrition_logs, sleep_logs, deload_tracker

Revision ID: 005
Revises: 004
Create Date: 2026-03-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop in reverse dependency order (children first)
    op.execute("DROP TABLE IF EXISTS exercise_logs CASCADE")
    op.execute("DROP TABLE IF EXISTS workout_sessions CASCADE")
    op.execute("DROP TABLE IF EXISTS workout_modifications CASCADE")
    op.execute("DROP TABLE IF EXISTS weigh_ins CASCADE")
    op.execute("DROP TABLE IF EXISTS nutrition_logs CASCADE")
    op.execute("DROP TABLE IF EXISTS sleep_logs CASCADE")
    op.execute("DROP TABLE IF EXISTS deload_tracker CASCADE")
    op.execute("DROP TABLE IF EXISTS training_blocks CASCADE")

    op.create_table(
        "training_blocks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("phase", sa.String(), nullable=False),
        sa.Column("start_date", sa.String(), nullable=False),
        sa.Column("end_date", sa.String(), nullable=True),
        sa.Column("calorie_target", sa.Integer(), nullable=True),
        sa.Column("protein_target", sa.Integer(), nullable=True),
        sa.Column("fat_min", sa.Integer(), nullable=True),
        sa.Column("fat_max", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_override", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "workout_sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("date", sa.String(), nullable=False),
        sa.Column("day_label", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("block_id", UUID(as_uuid=True), sa.ForeignKey("training_blocks.id"), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("deviation_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "exercise_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("session_id", UUID(as_uuid=True), sa.ForeignKey("workout_sessions.id"), nullable=False),
        sa.Column("exercise", sa.String(), nullable=False),
        sa.Column("sets", sa.Integer(), nullable=False),
        sa.Column("reps", sa.Integer(), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=False),
        sa.Column("rpe", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "workout_modifications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("exercise", sa.String(), nullable=False),
        sa.Column("modification_type", sa.String(), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("valid_from", sa.String(), nullable=False),
        sa.Column("valid_until", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "weigh_ins",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("date", sa.String(), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=False),
        sa.Column("block_id", UUID(as_uuid=True), sa.ForeignKey("training_blocks.id"), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

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

    op.create_table(
        "sleep_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("date", sa.String(), nullable=False, unique=True),
        sa.Column("hours", sa.Float(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "deload_tracker",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("cycle_start_date", sa.String(), nullable=False),
        sa.Column("weeks_completed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deload_done", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("deload_tracker")
    op.drop_table("sleep_logs")
    op.drop_table("nutrition_logs")
    op.drop_table("weigh_ins")
    op.drop_table("workout_modifications")
    op.drop_table("exercise_logs")
    op.drop_table("workout_sessions")
    op.drop_table("training_blocks")
