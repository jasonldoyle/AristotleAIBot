"""
Proactive nudge system for Plato bot.
Checks for schedule block endings, overdue tasks, and upcoming dates.
"""

from datetime import datetime, timedelta
from telegram.ext import ContextTypes
from plato.config import ALLOWED_USER_ID, logger
from plato.db import (
    get_planned_events_for_date, get_tasks_for_date,
    get_overdue_tasks, get_upcoming_dates,
)


async def check_for_nudges(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Periodic job that checks schedule blocks and sends nudges."""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        now = datetime.now()
        five_mins_ago = (now - timedelta(minutes=5)).strftime("%H:%M")
        now_str = now.strftime("%H:%M")

        events = get_planned_events_for_date(today)

        for event in events:
            end_time = event.get("end_time", "")
            if not end_time:
                continue

            if five_mins_ago <= end_time[:5] <= now_str and event["status"] == "planned":
                title = event["title"]
                msg = f"⏰ '{title}' just ended. How did it go?\n\nTell me what you actually did and I'll log it."

                await context.bot.send_message(
                    chat_id=ALLOWED_USER_ID,
                    text=msg
                )
                logger.info(f"Sent nudge for: {title}")

    except Exception as e:
        logger.error(f"Nudge check error: {e}")


async def morning_briefing(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Morning briefing — tasks, dates, and schedule for the day. Run at ~7:30am."""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        parts = []

        # Today's tasks
        tasks = get_tasks_for_date(today)
        if tasks:
            task_lines = []
            for t in tasks:
                icon = "🔴" if t.get("_overdue") else "🔁" if t.get("_recurring_due") else "📌"
                overdue = " ⚠️ OVERDUE" if t.get("_overdue") else ""
                task_lines.append(f"  {icon} {t['title']}{overdue}")
            parts.append("📋 Tasks:\n" + "\n".join(task_lines))

        # Upcoming dates (next 7 days)
        dates = get_upcoming_dates(7)
        if dates:
            date_lines = []
            for d in dates:
                age_str = f" (turning {d['_age']})" if d.get("_age") else ""
                if d["_days_until"] == 0:
                    date_lines.append(f"  🎂 TODAY: {d['title']}{age_str}")
                else:
                    date_lines.append(f"  📅 {d['title']}{age_str} in {d['_days_until']} days")
            parts.append("🗓️ Coming up:\n" + "\n".join(date_lines))

        # Today's schedule
        events = get_planned_events_for_date(today)
        if events:
            event_lines = []
            for e in events:
                event_lines.append(f"  ⬜ {e['start_time'][:5]}-{e['end_time'][:5]}: {e['title']}")
            parts.append("📅 Schedule:\n" + "\n".join(event_lines))

        if parts:
            msg = f"☀️ Morning, Jason. Here's your {datetime.now().strftime('%A')}:\n\n" + "\n\n".join(parts)
            await context.bot.send_message(chat_id=ALLOWED_USER_ID, text=msg)
            logger.info("Sent morning briefing")

    except Exception as e:
        logger.error(f"Morning briefing error: {e}")


async def overdue_check(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Afternoon check for overdue tasks. Run at ~2pm."""
    try:
        overdue = get_overdue_tasks()
        if overdue:
            lines = [f"  🔴 {t['title']} (due {t['due_date']})" for t in overdue]
            msg = f"⚠️ You have {len(overdue)} overdue task{'s' if len(overdue) > 1 else ''}:\n" + "\n".join(lines)
            msg += "\n\nDo them, reschedule, or tell me to skip."
            await context.bot.send_message(chat_id=ALLOWED_USER_ID, text=msg)
            logger.info(f"Sent overdue nudge: {len(overdue)} tasks")

    except Exception as e:
        logger.error(f"Overdue check error: {e}")