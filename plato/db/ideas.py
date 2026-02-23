from datetime import datetime, timedelta, timezone

from plato.config import SessionLocal
from plato.models import Idea

COOLING_PERIOD_DAYS = 14


def store_idea(idea: str, context: str = None) -> str:
    """Store a new idea. Returns the idea ID."""
    with SessionLocal() as session:
        entry = Idea(idea=idea, context=context, status="active")
        session.add(entry)
        session.commit()
        return str(entry.id)


def park_idea(idea_id: str) -> bool:
    """Park an active idea with a 14-day cooling period. Returns True if found."""
    now = datetime.now(timezone.utc)
    with SessionLocal() as session:
        idea = session.query(Idea).filter_by(id=idea_id, status="active").first()
        if not idea:
            return False
        idea.status = "parked"
        idea.parked_at = now
        idea.eligible_date = now + timedelta(days=COOLING_PERIOD_DAYS)
        session.commit()
        return True


def get_ideas(status: str = None) -> list[dict]:
    """Fetch ideas, optionally filtered by status."""
    now = datetime.now(timezone.utc)
    with SessionLocal() as session:
        query = session.query(Idea).order_by(Idea.created_at)
        if status:
            query = query.filter(Idea.status == status)
        rows = query.all()
        results = []
        for r in rows:
            entry = {
                "id": str(r.id),
                "idea": r.idea,
                "context": r.context,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            if r.status == "parked" and r.eligible_date:
                entry["eligible_date"] = r.eligible_date.isoformat()
                entry["is_eligible"] = now >= r.eligible_date
                entry["days_remaining"] = max(0, (r.eligible_date - now).days)
            results.append(entry)
        return results


def resolve_idea(idea_id: str, status: str, notes: str = None) -> bool:
    """Resolve an idea (approve/reject). Returns True if found."""
    if status not in ("approved", "rejected"):
        raise ValueError(f"Invalid status: {status}. Must be 'approved' or 'rejected'")
    with SessionLocal() as session:
        idea = session.query(Idea).filter_by(id=idea_id).first()
        if not idea:
            return False
        idea.status = status
        idea.resolution_notes = notes
        session.commit()
        return True


def format_ideas(ideas: list[dict]) -> str:
    """Format ideas for display."""
    if not ideas:
        return "No ideas stored."

    parts = []
    for i in ideas:
        line = f"- [{i['status'].upper()}] {i['idea']}"
        if i.get("context"):
            line += f" (context: {i['context']})"
        if i["status"] == "parked" and i.get("days_remaining") is not None:
            eligible = "ELIGIBLE" if i["is_eligible"] else f"{i['days_remaining']}d remaining"
            line += f" [{eligible}]"
        line += f"\n  ID: {i['id'][:8]}..."
        parts.append(line)
    return "\n".join(parts)
