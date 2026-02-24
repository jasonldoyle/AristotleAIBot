import uuid
from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, ForeignKey, func
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
