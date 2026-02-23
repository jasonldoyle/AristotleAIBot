from datetime import datetime, timezone
from collections import defaultdict

from plato.config import SessionLocal
from plato.models import SoulDoc

CATEGORY_ORDER = ["goal_lifetime", "goal_5yr", "goal_2yr", "goal_1yr", "philosophy", "rule"]


def get_soul_doc() -> dict[str, list[str]]:
    """Fetch all active soul doc entries, grouped by category."""
    with SessionLocal() as session:
        rows = (
            session.query(SoulDoc)
            .filter(SoulDoc.superseded_at.is_(None))
            .order_by(SoulDoc.created_at)
            .all()
        )
        grouped = defaultdict(list)
        for row in rows:
            grouped[row.category].append(row.content)
        return dict(grouped)


def add_soul_entry(category: str, content: str) -> str:
    """Insert a new soul doc entry. Returns the entry ID."""
    if category not in CATEGORY_ORDER:
        raise ValueError(f"Invalid category: {category}. Must be one of {CATEGORY_ORDER}")
    with SessionLocal() as session:
        entry = SoulDoc(category=category, content=content)
        session.add(entry)
        session.commit()
        return str(entry.id)


def supersede_soul_entry(entry_id: str) -> bool:
    """Mark a soul doc entry as superseded. Returns True if found."""
    with SessionLocal() as session:
        entry = session.query(SoulDoc).filter_by(id=entry_id).first()
        if not entry:
            return False
        entry.superseded_at = datetime.now(timezone.utc)
        session.commit()
        return True


def update_soul_entry(category: str, old_content: str, new_content: str) -> str:
    """Supersede the matching active entry in a category and add a new one. Returns new entry ID."""
    if category not in CATEGORY_ORDER:
        raise ValueError(f"Invalid category: {category}. Must be one of {CATEGORY_ORDER}")
    with SessionLocal() as session:
        # Find and supersede the old entry by matching category + content substring
        entries = (
            session.query(SoulDoc)
            .filter(SoulDoc.category == category, SoulDoc.superseded_at.is_(None))
            .all()
        )
        for entry in entries:
            if old_content.lower() in entry.content.lower():
                entry.superseded_at = datetime.now(timezone.utc)
                break
        # Add the refined version
        new_entry = SoulDoc(category=category, content=new_content)
        session.add(new_entry)
        session.commit()
        return str(new_entry.id)


def format_soul_doc(grouped: dict[str, list[str]]) -> str:
    """Format soul doc entries for display."""
    if not grouped:
        return "No soul doc entries yet."

    labels = {
        "goal_lifetime": "Lifetime Goals",
        "goal_5yr": "5-Year Goals",
        "goal_2yr": "2-Year Goals",
        "goal_1yr": "1-Year Goals",
        "philosophy": "Philosophy",
        "rule": "Rules",
    }
    parts = []
    for cat in CATEGORY_ORDER:
        entries = grouped.get(cat)
        if entries:
            parts.append(f"**{labels[cat]}**")
            for e in entries:
                parts.append(f"- {e}")
    return "\n".join(parts)
