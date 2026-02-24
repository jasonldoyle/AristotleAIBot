from datetime import datetime, timedelta
from plato.db.soul import get_soul_doc, format_soul_doc, CATEGORY_ORDER
from plato.db.projects import get_projects, format_projects_summary
from plato.db.schedule import get_schedule_for_date, format_todays_schedule, get_pending_plan
from plato.calendar import get_schedule_prompt


def _next_week_start() -> datetime:
    """Return next Monday, unless today is Monday."""
    today = datetime.now()
    weekday = today.weekday()
    if weekday == 0:
        return today.replace(hour=0, minute=0, second=0, microsecond=0)
    days_until_monday = 7 - weekday
    monday = today + timedelta(days=days_until_monday)
    return monday.replace(hour=0, minute=0, second=0, microsecond=0)


def get_base_prompt() -> str:
    """Return the base prompt with personality, soul doc, active projects, schedule context."""
    soul_doc = get_soul_doc()
    soul_section = format_soul_doc(soul_doc)

    projects = get_projects(status="active")
    projects_section = format_projects_summary(projects)

    today_str = datetime.now().strftime("%Y-%m-%d")
    todays_events = get_schedule_for_date(today_str)
    schedule_section = format_todays_schedule(todays_events)

    pending = get_pending_plan()
    pending_section = ""
    if pending:
        pending_section = f"\n\n## Pending Weekly Plan\nA plan for week of {pending['week_start']} is awaiting approval ({len(pending['events'])} events). Ask Jason if he wants to review/approve it."

    # Include scheduling template so Claude knows Jason's constraints when planning
    week_start = _next_week_start()
    scheduling_context = get_schedule_prompt(week_start, active_projects=projects)

    return f"""Current date and time: {datetime.now().strftime("%A %B %d, %Y %H:%M")}

You are Plato, Jason's personal AI mentor. You embody stoic wisdom and hold him accountable.

Your role:
- Be direct, honest, and occasionally challenging
- Celebrate genuine progress, but don't flatter
- Be concise but insightful
- Reference Jason's goals and principles when relevant
- When creating projects, check alignment with the soul doc
- Celebrate goal achievements in context of the bigger picture
- If no action is needed (just conversation), respond naturally

## Jason's Soul Doc
{soul_section}

## Active Projects
{projects_section}

## Today's Schedule
{schedule_section}{pending_section}

{scheduling_context}"""
