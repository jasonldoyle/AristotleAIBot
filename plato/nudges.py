"""
Proactive nudge system for Plato bot.
Checks if scheduled blocks have ended and prompts Jason for check-ins.
"""

from datetime import datetime, timedelta
from telegram.ext import ContextTypes
from plato.config import ALLOWED_USER_ID, logger
from plato.db import get_planned_events_for_date


async def check_for_nudges(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Periodic job that checks if a scheduled block just ended and sends a nudge."""
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