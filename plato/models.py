import uuid
from sqlalchemy import Column, String, Text, DateTime, func
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
