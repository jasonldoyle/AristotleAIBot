"""
Admin domain — tasks, recurring tasks, important dates.
"""

from datetime import datetime
from plato.db import (
    get_tasks_for_date, get_upcoming_tasks, get_upcoming_dates,
    get_overdue_tasks, get_recurring_tasks,
)


def get_action_schemas() -> str:
    return """
### ADMIN TASK ACTIONS:

**ADD TASK** - One-off task with optional due date
```json
{"action": "add_task", "title": "Buy mam's birthday gift", "due_date": "2026-02-14", "due_time": null, "category": "shopping", "priority": "high", "notes": null}
```
Categories: personal, shopping, health, admin, social. Priorities: low, normal, high, urgent.

**COMPLETE TASK** - Mark a task as done
```json
{"action": "complete_task", "task_fragment": "boots skincare"}
```

**SKIP TASK** - Skip a task
```json
{"action": "skip_task", "task_fragment": "boots skincare", "reason": "shop was closed"}
```

**DELETE TASK** - Remove a task entirely
```json
{"action": "delete_task", "task_fragment": "boots skincare"}
```

**ADD RECURRING** - Task that repeats weekly/monthly
```json
{"action": "add_recurring", "title": "Laundry", "recurring": "weekly", "recurring_day": "thursday", "category": "personal"}
```

**COMPLETE RECURRING** - Mark this week's/month's occurrence as done
```json
{"action": "complete_recurring", "task_fragment": "laundry"}
```

**DELETE RECURRING** - Remove a recurring task permanently
```json
{"action": "delete_recurring", "task_fragment": "laundry"}
```

**ADD IMPORTANT DATE** - Birthday, anniversary, deadline
```json
{"action": "add_date", "title": "Mam's birthday", "month": 3, "day": 15, "year": 1970, "category": "birthday", "reminder_days": 7, "notes": null}
```

**DELETE DATE** - Remove an important date
```json
{"action": "delete_date", "title_fragment": "Mam's birthday"}
```

**SHOW TASKS** - Display tasks
```json
{"action": "show_tasks", "scope": "today|upcoming|all", "days": 7}
```"""


def get_context() -> str:
    """Build admin task context — today's tasks, upcoming, recurring."""
    try:
        context = ""
        has_data = False

        # Today's tasks
        today_tasks = get_tasks_for_date()
        if today_tasks:
            has_data = True
            context += "\n## TODAY'S TASKS\n"
            for t in today_tasks:
                icon = "🔴" if t.get("_overdue") else "🔁" if t.get("_recurring_due") else "📌"
                priority = f" [{t['priority'].upper()}]" if t.get("priority") not in ("normal", None) else ""
                overdue = " ⚠️ OVERDUE" if t.get("_overdue") else ""
                context += f"  {icon} {t['title']}{priority}{overdue}\n"

        # Upcoming in next 7 days
        upcoming = get_upcoming_tasks(7)
        today_str = datetime.now().strftime("%Y-%m-%d")
        upcoming = [t for t in upcoming if t.get("due_date") != today_str]
        if upcoming:
            has_data = True
            context += "\n## UPCOMING TASKS (7 days)\n"
            for t in upcoming:
                context += f"  📌 {t['due_date']}: {t['title']}\n"

        # Upcoming important dates (30 days)
        dates = get_upcoming_dates(30)
        if dates:
            has_data = True
            context += "\n## UPCOMING DATES\n"
            for d in dates:
                age_str = f" (turning {d['_age']})" if d.get("_age") else ""
                if d["_days_until"] == 0:
                    context += f"  🎂 TODAY: {d['title']}{age_str}\n"
                elif d["_days_until"] <= d.get("reminder_days", 7):
                    context += f"  🎂 {d['_next_date']}: {d['title']}{age_str} — {d['_days_until']} days!\n"
                else:
                    context += f"  📅 {d['_next_date']}: {d['title']}{age_str} — {d['_days_until']} days\n"

        # Recurring tasks summary
        recurring = get_recurring_tasks()
        if recurring:
            has_data = True
            from plato.db.admin import DAY_NAMES
            context += "\n## RECURRING TASKS\n"
            for t in recurring:
                if t["recurring"] == "weekly":
                    day = DAY_NAMES.get(t.get("recurring_day"), "?")
                    context += f"  🔁 {t['title']} (every {day})\n"
                elif t["recurring"] == "monthly":
                    context += f"  🔁 {t['title']} (monthly, {t.get('recurring_day')}th)\n"
                else:
                    context += f"  🔁 {t['title']} ({t['recurring']})\n"

        if not has_data:
            return ""

        return context

    except Exception as e:
        return f"\n## ADMIN TASKS\n  ⚠️ Error loading tasks: {e}\n"
