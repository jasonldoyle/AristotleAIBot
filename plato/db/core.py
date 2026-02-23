from plato.config import SessionLocal
from plato.models import Conversation


def get_recent_conversations(limit: int = 10) -> list[dict]:
    """Fetch recent conversation history."""
    with SessionLocal() as session:
        rows = (
            session.query(Conversation)
            .order_by(Conversation.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {"role": r.role, "content": r.content}
            for r in reversed(rows)
        ]


def save_conversation(role: str, content: str) -> None:
    """Save a message to conversation history."""
    with SessionLocal() as session:
        session.add(Conversation(role=role, content=content))
        session.commit()


def clear_conversations() -> None:
    """Delete all conversation history."""
    with SessionLocal() as session:
        session.query(Conversation).delete()
        session.commit()
