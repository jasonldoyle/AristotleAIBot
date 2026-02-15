"""
Context builders for always-on brief context sections.
These provide Plato with ambient awareness regardless of domain.
"""

from datetime import datetime
from plato.db import (
    get_planned_events_for_date, get_overdue_tasks,
)


def get_today_schedule_brief() -> str:
    """Brief today's schedule — always included for time awareness."""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        today_events = get_planned_events_for_date(today)
        if not today_events:
            return ""
        context = "\n## TODAY'S SCHEDULE\n"
        status_icons = {
            "planned": "⬜", "completed": "✅", "partial": "🟡",
            "skipped": "❌", "audrey_time": "💕", "rescheduled": "🔄"
        }
        for e in today_events:
            icon = status_icons.get(e["status"], "⬜")
            context += f"  {icon} {e['start_time'][:5]}-{e['end_time'][:5]}: {e['title']} [{e['status']}]\n"
        return context
    except Exception:
        return ""


def get_overdue_tasks_brief() -> str:
    """Brief overdue tasks — always included for accountability."""
    try:
        overdue = get_overdue_tasks()
        if not overdue:
            return ""
        context = "\n## ⚠️ OVERDUE TASKS\n"
        for t in overdue:
            context += f"  🔴 {t['title']} (due {t['due_date']})\n"
        return context
    except Exception:
        return ""
