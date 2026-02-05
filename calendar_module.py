"""
PLATO BOT - CALENDAR INTEGRATION PATCH
=======================================
Add these changes to your plato_bot.py to enable weekly planning.

This file isn't run directly — it shows what to add and where.
"""

# ============== 1. ADD IMPORTS (top of plato_bot.py) ==============

from datetime import datetime, timedelta
from calendar_module import (
    get_calendar_service, 
    get_schedule_prompt, 
    clear_plato_events, 
    create_weekly_events,
    get_weekly_template
)


# ============== 2. ADD TO build_system_prompt() ==============
# After the existing context sections (soul doc, projects, patterns),
# add this to the system prompt string:

SCHEDULE_SYSTEM_ADDITION = """
## CALENDAR CAPABILITIES

You can plan Jason's weekly schedule. When he asks you to plan his week 
(or says things like "plan my week", "what should my week look like", 
"schedule my week"), respond with:

1. Your mentor perspective on priorities for the week (based on Soul Doc, 
   active goals, and recent progress)
2. A JSON action block with action "plan_week"

The plan_week action should contain an "events" array. Each event needs:
- date (YYYY-MM-DD)
- start (HH:MM) 
- end (HH:MM)
- title (specific, e.g. "CFA - Quantitative Methods Ch.4")
- description (optional focus notes)
- category (cfa|nitrogen|glowbook|plato|leetcode|rest|exercise|personal|citco)

SCHEDULING CONSTRAINTS:
- Weekdays: Citco 9-6 is untouchable
- Office days (check template): commute eats 7:30-9:00 and 18:00-19:30
- WFH days: morning block 7:30-9:00 is available
- Weekends: mam's guzheng school 9:15-10:45 and 19:00-20:30 are fixed
- Bed by 23:00
- Minimum 10 hrs/week CFA study
- Minimum 8 hrs/week side projects
- At least 3 exercise sessions
- Rest blocks every evening, Sunday evening kept light
"""


# ============== 3. ADD WEEK CONTEXT TO MESSAGES ==============
# When the user asks to plan their week, include the template.
# Add this function:

def handle_plan_week_context(user_message: str) -> str:
    """If user is asking to plan their week, add schedule context."""
    plan_triggers = ["plan my week", "plan the week", "schedule my week", 
                     "what should my week look like", "weekly plan",
                     "plan this week", "plan next week"]
    
    msg_lower = user_message.lower()
    
    for trigger in plan_triggers:
        if trigger in msg_lower:
            # Determine which week
            today = datetime.now()
            if "next week" in msg_lower:
                # Next Monday
                days_ahead = 7 - today.weekday()
                week_start = today + timedelta(days=days_ahead)
            else:
                # This week's Monday
                week_start = today - timedelta(days=today.weekday())
            
            week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
            return get_schedule_prompt(week_start)
    
    return ""


# ============== 4. MODIFY handle_message() ==============
# In your handle_message function, before the Claude API call:

"""
# Add schedule context if planning week
schedule_context = handle_plan_week_context(user_message)
if schedule_context:
    # Append to system prompt for this call
    system_prompt = system_prompt + schedule_context
"""


# ============== 5. ADD TO process_action() ==============
# Add this case to your action processing:

def process_plan_week_action(action_data: dict) -> str:
    """Process a plan_week action - create calendar events."""
    try:
        events = action_data.get("events", [])
        if not events:
            return "⚠️ No events in schedule."
        
        service = get_calendar_service()
        
        # Determine week start from first event
        first_date = datetime.strptime(events[0]["date"], "%Y-%m-%d")
        week_start = first_date - timedelta(days=first_date.weekday())
        
        # Clear existing Plato events for this week
        cleared = clear_plato_events(service, week_start)
        
        # Create new events
        created = create_weekly_events(service, events)
        
        return f"📅 Scheduled {created} events (cleared {cleared} old ones)."
    
    except Exception as e:
        logger.error(f"Calendar error: {e}")
        return f"⚠️ Calendar error: {e}"


# In your existing process_action() function, add:
"""
elif action == "plan_week":
    return process_plan_week_action(action_data)
"""


# ============== 6. UPDATE requirements.txt ==============
# Add these lines:
"""
google-api-python-client
google-auth-oauthlib
google-auth-httplib2
"""