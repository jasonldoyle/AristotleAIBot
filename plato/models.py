import uuid
from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, Float, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SoulDoc(Base):
    __tablename__ = "soul_doc"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    category = Column(String, nullable=False)  # goal_lifetime, goal_5yr, goal_2yr, goal_1yr, philosophy, rule
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    superseded_at = Column(DateTime(timezone=True), nullable=True)


class Idea(Base):
    __tablename__ = "ideas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    idea = Column(Text, nullable=False)
    context = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="active")  # active, parked, approved, rejected
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    parked_at = Column(DateTime(timezone=True), nullable=True)
    eligible_date = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    intent = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="active")  # active, paused, completed, abandoned
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ProjectGoal(Base):
    __tablename__ = "project_goals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    timeframe = Column(String, nullable=False)  # weekly, monthly, quarterly, milestone
    goal_text = Column(Text, nullable=False)
    target_date = Column(DateTime(timezone=True), nullable=True)
    achieved = Column(Boolean, default=False, server_default="false")
    achieved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ProjectLog(Base):
    __tablename__ = "project_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    summary = Column(Text, nullable=False)
    duration_mins = Column(Integer, nullable=True)
    mood = Column(String, nullable=True)  # productive, frustrated, flow, etc.
    logged_at = Column(DateTime(timezone=True), server_default=func.now())


class ScheduleEvent(Base):
    __tablename__ = "schedule_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    date = Column(String, nullable=False)               # "YYYY-MM-DD"
    start_time = Column(String, nullable=False)          # "HH:MM"
    end_time = Column(String, nullable=False)            # "HH:MM"
    title = Column(String, nullable=False)
    category = Column(String, nullable=True)             # cfa, nitrogen, exercise, rest, etc.
    status = Column(String, default="scheduled")         # scheduled, completed, deviated, cancelled
    deviation_reason = Column(Text, nullable=True)
    week_start = Column(String, nullable=True)           # Monday of the week
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PendingPlan(Base):
    __tablename__ = "pending_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    week_start = Column(String, nullable=False)          # "YYYY-MM-DD" Monday
    events_json = Column(Text, nullable=False)           # JSON string of events array
    status = Column(String, default="pending")           # pending, approved, rejected
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)


# --- Fitness models (Phase 4) ---

class TrainingBlock(Base):
    __tablename__ = "training_blocks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    name = Column(String, nullable=False)                    # e.g. "Bulk 1", "Mini-Cut 1"
    phase = Column(String, nullable=False)                   # bulk, mini_cut, final_cut, maintenance
    start_date = Column(String, nullable=False)              # "YYYY-MM-DD"
    end_date = Column(String, nullable=True)
    calorie_target = Column(Integer, nullable=True)
    protein_target = Column(Integer, nullable=True)
    fat_min = Column(Integer, nullable=True)
    fat_max = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    is_override = Column(Boolean, default=False, server_default="false")
    status = Column(String, nullable=False, default="active")  # active, completed
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class WorkoutSession(Base):
    __tablename__ = "workout_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    date = Column(String, nullable=False)                    # "YYYY-MM-DD"
    day_label = Column(String, nullable=False)               # day1_chest, day2_back, day3_legs, day4_shoulders
    status = Column(String, nullable=False)                  # completed, partial, missed, deload
    block_id = Column(UUID(as_uuid=True), ForeignKey("training_blocks.id"), nullable=True)
    feedback = Column(Text, nullable=True)
    deviation_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ExerciseLog(Base):
    __tablename__ = "exercise_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    session_id = Column(UUID(as_uuid=True), ForeignKey("workout_sessions.id"), nullable=False)
    exercise = Column(String, nullable=False)                # slug e.g. "incline_bb_press"
    sets = Column(Integer, nullable=False)
    reps = Column(Integer, nullable=False)
    weight_kg = Column(Float, nullable=False)
    rpe = Column(Integer, nullable=True)                     # 1-10
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class WorkoutModification(Base):
    __tablename__ = "workout_modifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    exercise = Column(String, nullable=False)                # exercise slug
    modification_type = Column(String, nullable=False)       # reduce_volume, increase_volume, swap, adjust_weight, skip, custom
    detail = Column(Text, nullable=False)                    # e.g. "3 sets instead of 4"
    reason = Column(Text, nullable=True)
    valid_from = Column(String, nullable=False)              # "YYYY-MM-DD"
    valid_until = Column(String, nullable=True)              # null = until cancelled
    status = Column(String, nullable=False, default="active")  # active, expired, cancelled
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class WeighIn(Base):
    __tablename__ = "weigh_ins"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    date = Column(String, nullable=False)                    # "YYYY-MM-DD"
    weight_kg = Column(Float, nullable=False)
    block_id = Column(UUID(as_uuid=True), ForeignKey("training_blocks.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class NutritionLog(Base):
    __tablename__ = "nutrition_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    month = Column(String, nullable=False, unique=True)      # "YYYY-MM"
    avg_calories = Column(Integer, nullable=True)
    avg_protein_g = Column(Integer, nullable=True)
    avg_carbs_g = Column(Integer, nullable=True)
    avg_fat_g = Column(Integer, nullable=True)
    block_id = Column(UUID(as_uuid=True), ForeignKey("training_blocks.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SleepLog(Base):
    __tablename__ = "sleep_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    date = Column(String, nullable=False, unique=True)       # "YYYY-MM-DD"
    hours = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DeloadTracker(Base):
    __tablename__ = "deload_tracker"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    cycle_start_date = Column(String, nullable=False)        # "YYYY-MM-DD"
    weeks_completed = Column(Integer, nullable=False, default=0)
    deload_done = Column(Boolean, nullable=False, default=False, server_default="false")
    status = Column(String, nullable=False, default="active")  # active, completed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
