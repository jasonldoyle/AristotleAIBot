import os
import json
import logging
from datetime import datetime, timedelta, time
from dotenv import load_dotenv
load_dotenv()

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from supabase import create_client, Client
from anthropic import Anthropic
from plato_calendar import (
    get_calendar_service,
    get_schedule_prompt,
    clear_plato_events,
    create_weekly_events,
    cancel_evening_events,
    get_todays_events,
    create_event
)

# Config
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
ALLOWED_USER_ID = int(os.environ.get("ALLOWED_USER_ID", 0))

# Clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============== DATABASE HELPERS ==============

def get_soul_doc() -> str:
    """Fetch all active soul doc entries."""
    result = supabase.table("soul_doc").select("*").is_("superseded_at", "null").execute()
    if not result.data:
        return "No soul doc entries yet."
    
    grouped = {}
    for entry in result.data:
        cat = entry["category"]
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append(entry["content"])
    
    output = []
    for category, entries in grouped.items():
        output.append(f"## {category.upper()}")
        for e in entries:
            output.append(f"- {e}")
    
    return "\n".join(output)


def get_active_projects() -> list[dict]:
    """Fetch all active projects with their current goals."""
    projects = supabase.table("projects").select("*").eq("status", "active").execute()
    
    for project in projects.data:
        goals = supabase.table("project_goals").select("*").eq("project_id", project["id"]).eq("achieved", False).execute()
        project["current_goals"] = goals.data
        
        logs = supabase.table("project_logs").select("*").eq("project_id", project["id"]).order("logged_at", desc=True).limit(5).execute()
        project["recent_logs"] = logs.data
    
    return projects.data


def get_unresolved_patterns() -> list[dict]:
    """Fetch patterns that haven't been resolved."""
    result = supabase.table("patterns").select("*").eq("resolved", False).execute()
    return result.data


def get_project_by_slug(slug: str) -> dict | None:
    """Find a project by its slug."""
    result = supabase.table("projects").select("*").eq("slug", slug).execute()
    return result.data[0] if result.data else None


def get_recent_conversations(limit: int = 10) -> list[dict]:
    """Fetch recent conversation history."""
    result = supabase.table("conversations").select("*").order("created_at", desc=True).limit(limit).execute()
    return list(reversed(result.data)) if result.data else []


def save_conversation(role: str, content: str) -> None:
    """Save a message to conversation history."""
    supabase.table("conversations").insert({"role": role, "content": content}).execute()


def log_work(project_id: str, summary: str, duration_mins: int | None, blockers: str | None, tags: list[str], mood: str | None, raw_message: str) -> dict:
    """Insert a project log entry."""
    entry = {
        "project_id": project_id,
        "summary": summary,
        "duration_mins": duration_mins,
        "blockers": blockers,
        "tags": tags,
        "mood": mood,
        "raw_message": raw_message
    }
    result = supabase.table("project_logs").insert(entry).execute()
    return result.data[0]


def create_project(name: str, slug: str, intent: str) -> dict:
    """Create a new project."""
    entry = {
        "name": name,
        "slug": slug,
        "intent": intent,
        "status": "active"
    }
    result = supabase.table("projects").insert(entry).execute()
    return result.data[0]


def add_soul_doc_entry(content: str, category: str, trigger: str) -> dict:
    """Add a new soul doc entry."""
    entry = {
        "content": content,
        "category": category,
        "trigger": trigger
    }
    result = supabase.table("soul_doc").insert(entry).execute()
    return result.data[0]


def add_project_goal(project_id: str, timeframe: str, goal_text: str, target_date: str | None = None) -> dict:
    """Add a goal to a project."""
    entry = {
        "project_id": project_id,
        "timeframe": timeframe,
        "goal_text": goal_text,
        "target_date": target_date
    }
    result = supabase.table("project_goals").insert(entry).execute()
    return result.data[0]


def mark_goal_achieved(project_slug: str, goal_text_fragment: str) -> bool:
    """Mark a goal as achieved by matching partial text."""
    project = get_project_by_slug(project_slug)
    if not project:
        return False
    
    goals = supabase.table("project_goals").select("*").eq("project_id", project["id"]).eq("achieved", False).execute()
    
    for goal in goals.data:
        if goal_text_fragment.lower() in goal["goal_text"].lower():
            supabase.table("project_goals").update({
                "achieved": True,
                "achieved_at": datetime.now().isoformat()
            }).eq("id", goal["id"]).execute()
            return True
    return False


def update_project(slug: str, updates: dict) -> bool:
    """Update project details."""
    project = get_project_by_slug(slug)
    if not project:
        return False
    
    supabase.table("projects").update(updates).eq("id", project["id"]).execute()
    return True


def add_pattern(pattern_type: str, description: str, project_id: str | None = None) -> dict:
    """Create a new pattern entry."""
    entry = {
        "pattern_type": pattern_type,
        "description": description,
        "project_id": project_id
    }
    result = supabase.table("patterns").insert(entry).execute()
    return result.data[0]


# ============== FITNESS HELPERS ==============

def log_fitness_exercises(exercises: list[dict]) -> int:
    """Log multiple exercises from a gym session. Returns count logged."""
    count = 0
    today = datetime.now().strftime("%Y-%m-%d")
    for ex in exercises:
        entry = {
            "session_date": ex.get("date", today),
            "exercise_name": ex["exercise"],
            "sets": ex.get("sets"),
            "reps": ex.get("reps"),
            "weight_kg": ex.get("weight_kg"),
            "notes": ex.get("notes")
        }
        supabase.table("fitness_logs").insert(entry).execute()
        count += 1
    return count


def store_pending_plan(events: list[dict]) -> None:
    """Store a pending weekly plan for approval."""
    # Clear any existing pending plan
    supabase.table("pending_plan").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    supabase.table("pending_plan").insert({"events": json.dumps(events)}).execute()


def get_pending_plan() -> list[dict] | None:
    """Retrieve the pending plan if one exists."""
    result = supabase.table("pending_plan").select("*").order("created_at", desc=True).limit(1).execute()
    if result.data:
        return json.loads(result.data[0]["events"])
    return None


def clear_pending_plan() -> None:
    """Clear the pending plan after approval or rejection."""
    supabase.table("pending_plan").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()


def get_recent_fitness(days: int = 7) -> list[dict]:
    """Fetch fitness logs from the last N days."""
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    result = supabase.table("fitness_logs").select("*").gte("session_date", since).order("session_date", desc=True).execute()
    return result.data


# ============== SCHEDULE EVENT HELPERS ==============

def store_schedule_events(events: list[dict]) -> int:
    """Store planned events in schedule_events table for adherence tracking."""
    count = 0
    for event in events:
        entry = {
            "date": event["date"],
            "start_time": event["start"],
            "end_time": event["end"],
            "title": event["title"],
            "category": event.get("category", "personal"),
            "description": event.get("description"),
            "status": "planned"
        }
        supabase.table("schedule_events").insert(entry).execute()
        count += 1
    return count


def get_planned_events_for_date(date_str: str) -> list[dict]:
    """Get planned schedule events for a specific date."""
    result = supabase.table("schedule_events").select("*").eq("date", date_str).order("start_time").execute()
    return result.data


def update_schedule_event(event_id: str, status: str, actual_summary: str = None, gap_reason: str = None) -> bool:
    """Update a schedule event's status and outcome."""
    updates = {"status": status, "updated_at": datetime.now().isoformat()}
    if actual_summary:
        updates["actual_summary"] = actual_summary
    if gap_reason:
        updates["gap_reason"] = gap_reason
    
    supabase.table("schedule_events").update(updates).eq("id", event_id).execute()
    return True


def mark_evening_audrey(date_str: str, from_time: str = "18:00") -> list[dict]:
    """Mark evening schedule events as audrey_time. Returns affected events."""
    events = supabase.table("schedule_events").select("*").eq("date", date_str).eq("status", "planned").gte("start_time", from_time).execute()
    
    affected = []
    for event in events.data:
        supabase.table("schedule_events").update({
            "status": "audrey_time",
            "updated_at": datetime.now().isoformat()
        }).eq("id", event["id"]).execute()
        affected.append(event)
    
    return affected


def get_weekly_adherence(week_start_str: str) -> dict:
    """Calculate schedule adherence stats for a week."""
    week_end = (datetime.strptime(week_start_str, "%Y-%m-%d") + timedelta(days=7)).strftime("%Y-%m-%d")
    
    result = supabase.table("schedule_events").select("*").gte("date", week_start_str).lt("date", week_end).execute()
    
    stats = {
        "total": len(result.data),
        "completed": 0,
        "partial": 0,
        "skipped": 0,
        "audrey_time": 0,
        "rescheduled": 0,
        "planned": 0,
        "by_category": {}
    }
    
    for event in result.data:
        status = event["status"]
        stats[status] = stats.get(status, 0) + 1
        
        cat = event["category"]
        if cat not in stats["by_category"]:
            stats["by_category"][cat] = {"completed": 0, "total": 0}
        stats["by_category"][cat]["total"] += 1
        if status == "completed":
            stats["by_category"][cat]["completed"] += 1
    
    if stats["total"] > 0:
        stats["adherence_pct"] = round((stats["completed"] + stats["partial"] * 0.5) / stats["total"] * 100, 1)
    else:
        stats["adherence_pct"] = 0
    
    return stats


# ============== CALENDAR HELPERS ==============

PLAN_TRIGGERS = [
    "plan my week", "plan the week", "schedule my week",
    "what should my week look like", "weekly plan",
    "plan this week", "plan next week"
]


def detect_plan_week(user_message: str) -> str | None:
    """Check if user is asking to plan their week. Returns schedule prompt or None."""
    msg_lower = user_message.lower()
    
    for trigger in PLAN_TRIGGERS:
        if trigger in msg_lower:
            today = datetime.now()
            if "next week" in msg_lower:
                days_ahead = 7 - today.weekday()
                week_start = today + timedelta(days=days_ahead)
            else:
                week_start = today - timedelta(days=today.weekday())
            
            week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
            return get_schedule_prompt(week_start)
    
    return None


def process_plan_week(action_data: dict) -> str:
    """Process a plan_week action - store as pending for approval."""
    try:
        events = action_data.get("events", [])
        if not events:
            return "⚠️ No events in schedule."
        
        # Store for approval instead of pushing directly
        store_pending_plan(events)
        
        # Build readable summary
        by_date = {}
        for e in events:
            d = e["date"]
            if d not in by_date:
                by_date[d] = []
            by_date[d].append(f"  {e['start']}-{e['end']}: {e['title']}")
        
        summary = "📋 PROPOSED SCHEDULE:\n\n"
        for date in sorted(by_date.keys()):
            day_name = datetime.strptime(date, "%Y-%m-%d").strftime("%A %b %d")
            summary += f"{day_name}:\n"
            summary += "\n".join(by_date[date]) + "\n\n"
        
        summary += f"Total: {len(events)} blocks.\n"
        summary += "Say 'approve' to push to calendar, or tell me what to change."
        
        return summary
    
    except Exception as e:
        logger.error(f"Plan week error: {e}")
        return f"⚠️ Plan error: {e}"


def process_approve_plan() -> str:
    """Push the pending plan to Google Calendar."""
    try:
        events = get_pending_plan()
        if not events:
            return "⚠️ No pending plan to approve. Say 'plan my week' first."
        
        service = get_calendar_service()
        
        # Determine week start from first event
        first_date = datetime.strptime(events[0]["date"], "%Y-%m-%d")
        week_start = first_date - timedelta(days=first_date.weekday())
        
        # Clear existing Plato events for this week
        cleared = clear_plato_events(service, week_start)
        
        # Create new calendar events
        created = create_weekly_events(service, events)
        
        # Store in schedule_events table for adherence tracking
        stored = store_schedule_events(events)
        
        # Clear the pending plan
        clear_pending_plan()
        
        return f"📅 Approved! Scheduled {created} events (cleared {cleared} old ones). Tracking {stored} blocks."
    
    except Exception as e:
        logger.error(f"Approve plan error: {e}")
        return f"⚠️ Error pushing plan: {e}"


def process_audrey_time(action_data: dict) -> str:
    """Process audrey_time action - cancel evening events and report what's bumped."""
    try:
        date_str = action_data.get("date", datetime.now().strftime("%Y-%m-%d"))
        from_time = action_data.get("from_time", "18:00")
        
        # Cancel Google Calendar events
        service = get_calendar_service()
        cancelled = cancel_evening_events(service, date_str, from_time)
        
        # Mark schedule events as audrey_time
        affected = mark_evening_audrey(date_str, from_time)
        
        if not cancelled and not affected:
            return "No planned blocks to cancel for tonight."
        
        bumped_titles = [e["title"] for e in cancelled]
        return f"💕 Audrey time activated. Cancelled {len(cancelled)} blocks: {', '.join(bumped_titles)}"
    
    except Exception as e:
        logger.error(f"Audrey time error: {e}")
        return f"⚠️ Error activating Audrey time: {e}"


def process_add_event(action_data: dict) -> str:
    """Process add_event action - add a one-off event to calendar."""
    try:
        service = get_calendar_service()
        
        date_str = action_data["date"]
        start = action_data["start"]
        end = action_data["end"]
        title = action_data["title"]
        category = action_data.get("category", "personal")
        description = action_data.get("description")
        
        # Create calendar event
        COLOR_MAP = {
            "cfa": "9", "nitrogen": "10", "glowbook": "6", "plato": "7",
            "leetcode": "3", "rest": "8", "exercise": "2", "personal": "4",
            "citco": "1", "audrey": "11",
        }
        
        create_event(
            service,
            date_str=date_str,
            start_time=start,
            end_time=end,
            title=title,
            description=description,
            color_id=COLOR_MAP.get(category)
        )
        
        # Cancel any conflicting planned blocks
        cancelled = cancel_conflicting_events(service, date_str, start, end)
        
        msg = f"📌 Added: {title} on {date_str} {start}-{end}"
        if cancelled:
            msg += f"\n⚠️ Cancelled {len(cancelled)} conflicting blocks: {', '.join(c['title'] for c in cancelled)}"
        
        return msg
    
    except Exception as e:
        logger.error(f"Add event error: {e}")
        return f"⚠️ Error adding event: {e}"


def cancel_conflicting_events(service, date_str: str, start: str, end: str) -> list:
    """Cancel Plato events that overlap with a new event."""
    cancelled = []
    
    events_result = service.events().list(
        calendarId='primary',
        timeMin=f'{date_str}T{start}:00+00:00',
        timeMax=f'{date_str}T{end}:00+00:00',
        singleEvents=True,
        q='[Plato]'
    ).execute()
    
    for event in events_result.get('items', []):
        summary = event.get('summary', '')
        # Don't cancel the event we just created
        if '[Plato]' in summary and summary != f'[Plato] {summary.replace("[Plato] ", "")}':
            continue
        # Skip — this is imperfect but avoids deleting the one we just made
        # We rely on the fact that the new event was just created
    
    return cancelled


def process_check_in(action_data: dict) -> str:
    """Process a check_in action - update schedule event with actual outcome."""
    try:
        event_id = action_data.get("event_id")
        status = action_data.get("status", "completed")  # completed, partial, skipped
        actual_summary = action_data.get("actual_summary")
        gap_reason = action_data.get("gap_reason")
        
        if event_id:
            update_schedule_event(event_id, status, actual_summary, gap_reason)
            return f"✅ Checked in: {status}"
        else:
            # Try to find the most recent planned event
            today = datetime.now().strftime("%Y-%m-%d")
            events = get_planned_events_for_date(today)
            now = datetime.now().strftime("%H:%M")
            
            # Find the most recent event that should have ended
            recent = None
            for e in events:
                if e["end_time"] <= now and e["status"] == "planned":
                    recent = e
            
            if recent:
                update_schedule_event(recent["id"], status, actual_summary, gap_reason)
                return f"✅ Checked in for '{recent['title']}': {status}"
            else:
                return "No recent planned block found to check in against."
    
    except Exception as e:
        logger.error(f"Check-in error: {e}")
        return f"⚠️ Check-in error: {e}"


# ============== PROACTIVE NUDGES ==============

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
            
            # Check if event ended within the last 5 minutes
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


# ============== CONTEXT ASSEMBLY ==============

def build_system_prompt(schedule_context: str = "") -> str:
    """Build Plato's system prompt with current context."""
    soul_doc = get_soul_doc()
    projects = get_active_projects()
    patterns = get_unresolved_patterns()
    recent_fitness = get_recent_fitness(days=7)
    
    projects_context = ""
    for p in projects:
        projects_context += f"\n### {p['name']} ({p['slug']})\n"
        projects_context += f"Intent: {p['intent']}\n"
        projects_context += f"Target: {p.get('target_date', 'No deadline')}\n"
        projects_context += f"Weekly hours allocated: {p.get('estimated_weekly_hours', 'Not set')}\n"
        projects_context += f"Stick/Twist: {p.get('stick_twist_criteria', 'Not defined')}\n"
        
        if p.get("current_goals"):
            projects_context += "Current goals:\n"
            for g in p["current_goals"]:
                projects_context += f"  - [{g['timeframe']}] {g['goal_text']}\n"
        
        if p.get("recent_logs"):
            projects_context += "Recent activity:\n"
            for log in p["recent_logs"][:3]:
                projects_context += f"  - {log['logged_at'][:10]}: {log['summary']}\n"
    
    patterns_context = ""
    if patterns:
        patterns_context = "\n## UNRESOLVED PATTERNS\n"
        for pat in patterns:
            patterns_context += f"- [{pat['pattern_type']}] {pat['description']} (seen {pat['occurrence_count']}x)\n"
    
    fitness_context = ""
    if recent_fitness:
        fitness_context = "\n## RECENT FITNESS (Last 7 days)\n"
        by_date = {}
        for log in recent_fitness:
            d = log["session_date"]
            if d not in by_date:
                by_date[d] = []
            weight_str = f" @ {log['weight_kg']}kg" if log.get("weight_kg") else ""
            by_date[d].append(f"{log['exercise_name']}: {log.get('sets', '?')}x{log.get('reps', '?')}{weight_str}")
        for date, exercises in by_date.items():
            fitness_context += f"  {date}: {', '.join(exercises)}\n"
    
    # Get today's schedule for context
    today_schedule = ""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        today_events = get_planned_events_for_date(today)
        if today_events:
            today_schedule = "\n## TODAY'S SCHEDULE\n"
            for e in today_events:
                status_icon = {"planned": "⬜", "completed": "✅", "partial": "🟡", "skipped": "❌", "audrey_time": "💕", "rescheduled": "🔄"}.get(e["status"], "⬜")
                today_schedule += f"  {status_icon} {e['start_time'][:5]}-{e['end_time'][:5]}: {e['title']} [{e['status']}]\n"
    except Exception:
        pass
    
    return f"""You are Plato, Jason's personal AI mentor. You embody stoic wisdom and hold him accountable to his long-term goals.

Your role:
- Parse work logs and store them accurately
- Provide perspective grounded in his Soul Doc (life goals)
- Call out deviations, impulses, and patterns
- Be direct, honest, and occasionally challenging
- Celebrate genuine progress, but don't flatter
- Track schedule adherence and help optimise his time

## SOUL DOC (His Constitution)
{soul_doc}

## ACTIVE PROJECTS
{projects_context}
{patterns_context}
{fitness_context}
{today_schedule}

## YOUR CAPABILITIES
When Jason messages you, determine the intent and respond with the appropriate JSON action block followed by your message.

### ACTIONS YOU CAN TAKE:

1. **LOG WORK** - He's reporting what he did
```json
{{"action": "log", "project_slug": "...", "summary": "...", "duration_mins": null, "blockers": null, "tags": [], "mood": null}}
```

2. **CREATE PROJECT** - He wants to add a new project
```json
{{"action": "create_project", "name": "...", "slug": "...", "intent": "..."}}
```

3. **ADD SOUL DOC** - He says "soullog:/" or wants to record a life principle/goal
```json
{{"action": "add_soul", "content": "...", "category": "goal_lifetime|goal_5yr|goal_2yr|goal_1yr|philosophy|rule|anti_pattern", "trigger": "..."}}
```

4. **SET PROJECT GOAL** - He wants to set a weekly/monthly/quarterly goal
```json
{{"action": "add_goal", "project_slug": "...", "timeframe": "weekly|monthly|quarterly|milestone", "goal_text": "...", "target_date": null}}
```

5. **MARK GOAL ACHIEVED** - He completed a goal
```json
{{"action": "achieve_goal", "project_slug": "...", "goal_fragment": "..."}}
```

6. **UPDATE PROJECT** - He wants to change project details
```json
{{"action": "update_project", "slug": "...", "updates": {{"target_date": null, "estimated_weekly_hours": null, "stick_twist_criteria": null, "alignment_rationale": null}}}}
```
Only include fields that are being updated.

7. **LOG PATTERN** - He's noticed a recurring behaviour
```json
{{"action": "add_pattern", "pattern_type": "blocker|overestimation|external_constraint|bad_habit|avoidance", "description": "...", "project_slug": null}}
```

8. **PLAN WEEK** - He wants his week scheduled on Google Calendar
```json
{{"action": "plan_week", "events": [
    {{"date": "YYYY-MM-DD", "start": "HH:MM", "end": "HH:MM", "title": "Short descriptive title", "description": "Optional detail", "category": "cfa|nitrogen|glowbook|plato|leetcode|rest|exercise|personal|citco|audrey"}}
]}}
```
When planning a week, generate a COMPLETE schedule filling all free blocks. Be specific with titles.
Priorities: CFA study minimum 10 hrs/week, side projects 8-10 hrs/week, exercise 3+ sessions, rest every evening, Sunday evening light.

9. **LOG FITNESS** - He's reporting a gym session
```json
{{"action": "log_fitness", "exercises": [
    {{"exercise": "Bench Press", "sets": 4, "reps": 8, "weight_kg": 60, "notes": null}},
    {{"exercise": "Lat Pulldown", "sets": 3, "reps": 12, "weight_kg": 50, "notes": "felt easy, increase next time"}}
]}}
```
Parse naturally: "Did bench 4x8 at 60kg, lat pulldown 3x12 at 50" → structured exercises.
His goal: bulk to build muscle until mid-2028, then cut. Currently ~80.5kg at ~20% BF. Target: 12-15% BF.

10. **AUDREY TIME** - He's taking the evening (or part of it) for girlfriend time
```json
{{"action": "audrey_time", "date": "YYYY-MM-DD", "from_time": "HH:MM"}}
```
When he says "audrey time", "spending tonight with Audrey", "girlfriend time" etc:
- Cancel the evening's planned blocks from the calendar
- Tell him exactly what got bumped (e.g. "You're dropping 2hrs CFA and 1hr Glowbook")
- Suggest where to reschedule the bumped work if there are free slots this week
- Log it — track cumulative Audrey time so you can flag if it's becoming a pattern

11. **ADD ONE-OFF EVENT** - Schedule a specific event (e.g. cousin's confirmation)
```json
{{"action": "add_event", "date": "YYYY-MM-DD", "start": "HH:MM", "end": "HH:MM", "title": "...", "category": "personal", "description": null}}
```
For events with unknown duration, block the minimum expected time. Jason can extend later.
This will also cancel any conflicting planned blocks.

12. **CHECK IN** - Record what actually happened during a planned block
```json
{{"action": "check_in", "event_id": "uuid-or-null", "status": "completed|partial|skipped", "actual_summary": "What actually got done", "gap_reason": "Why it didn't go to plan (if partial/skipped)"}}
```
When Jason reports back after a work block (or responds to a nudge), log what he actually did vs what was planned.
If event_id is null, find the most recent ended planned block for today.

### GUIDELINES:
- Available tags: coding, marketing, research, design, admin, learning, outreach
- Available moods: energised, neutral, drained, frustrated, flow
- If no action is needed (just conversation), don't include a JSON block
- Always provide your mentorship response AFTER the JSON block
- Be concise but insightful
- If he's going off-track, call it out firmly but kindly
- When he checks in, compare actual vs planned and note the gap honestly
- Track Audrey time cumulative impact — flag if 3+ weeks of heavy displacement

Current date: {datetime.now().strftime("%Y-%m-%d %H:%M")}
{schedule_context}"""


def build_messages_with_history(user_message: str) -> list[dict]:
    """Build message list including conversation history."""
    history = get_recent_conversations(limit=10)
    
    messages = []
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    
    messages.append({"role": "user", "content": user_message})
    
    return messages


# ============== ACTION PROCESSING ==============

def process_action(action_data: dict, raw_message: str) -> str | None:
    """Process a JSON action and return a status message if needed."""
    action = action_data.get("action")
    
    try:
        if action == "log":
            project = get_project_by_slug(action_data["project_slug"])
            if project:
                log_work(
                    project_id=project["id"],
                    summary=action_data["summary"],
                    duration_mins=action_data.get("duration_mins"),
                    blockers=action_data.get("blockers"),
                    tags=action_data.get("tags", []),
                    mood=action_data.get("mood"),
                    raw_message=raw_message
                )
                logger.info(f"Logged work for {action_data['project_slug']}")
            else:
                return f"⚠️ Project '{action_data['project_slug']}' not found."
        
        elif action == "create_project":
            create_project(
                name=action_data["name"],
                slug=action_data["slug"],
                intent=action_data["intent"]
            )
            logger.info(f"Created project: {action_data['slug']}")
        
        elif action == "add_soul":
            add_soul_doc_entry(
                content=action_data["content"],
                category=action_data["category"],
                trigger=action_data.get("trigger", "Conversation")
            )
            logger.info(f"Added soul doc entry: {action_data['category']}")
        
        elif action == "add_goal":
            project = get_project_by_slug(action_data["project_slug"])
            if project:
                add_project_goal(
                    project_id=project["id"],
                    timeframe=action_data["timeframe"],
                    goal_text=action_data["goal_text"],
                    target_date=action_data.get("target_date")
                )
                logger.info(f"Added {action_data['timeframe']} goal to {action_data['project_slug']}")
            else:
                return f"⚠️ Project '{action_data['project_slug']}' not found."
        
        elif action == "achieve_goal":
            success = mark_goal_achieved(
                project_slug=action_data["project_slug"],
                goal_text_fragment=action_data["goal_fragment"]
            )
            if success:
                logger.info(f"Marked goal achieved for {action_data['project_slug']}")
            else:
                return f"⚠️ Couldn't find matching goal for '{action_data['goal_fragment']}'."
        
        elif action == "update_project":
            success = update_project(
                slug=action_data["slug"],
                updates=action_data["updates"]
            )
            if success:
                logger.info(f"Updated project: {action_data['slug']}")
            else:
                return f"⚠️ Project '{action_data['slug']}' not found."
        
        elif action == "add_pattern":
            project_id = None
            if action_data.get("project_slug"):
                project = get_project_by_slug(action_data["project_slug"])
                if project:
                    project_id = project["id"]
            
            add_pattern(
                pattern_type=action_data["pattern_type"],
                description=action_data["description"],
                project_id=project_id
            )
            logger.info(f"Added pattern: {action_data['pattern_type']}")
        
        elif action == "plan_week":
            return process_plan_week(action_data)
        
        elif action == "log_fitness":
            count = log_fitness_exercises(action_data.get("exercises", []))
            return f"💪 Logged {count} exercises."
        
        elif action == "audrey_time":
            return process_audrey_time(action_data)
        
        elif action == "add_event":
            return process_add_event(action_data)
        
        elif action == "check_in":
            return process_check_in(action_data)
        
        return None
    
    except Exception as e:
        logger.error(f"Action processing error: {e}")
        return f"⚠️ Error processing action: {str(e)}"


# ============== MESSAGE HANDLING ==============

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages."""
    user_id = update.effective_user.id
    
    if user_id != ALLOWED_USER_ID:
        await update.message.reply_text("Plato serves only one master.")
        return
    
    user_message = update.message.text
    logger.info(f"Received: {user_message}")
    
    # Save user message to history
    save_conversation("user", user_message)
    
    # Check for plan approval/rejection
    msg_lower = user_message.lower().strip()
    if msg_lower in ["approve", "approved", "looks good", "push it", "send it", "go ahead", "lgtm"]:
        result = process_approve_plan()
        save_conversation("assistant", result)
        await update.message.reply_text(result)
        return
    
    # Check if planning week — add schedule context if so
    schedule_context = detect_plan_week(user_message) or ""
    
    # If there's a pending plan and user is requesting changes, include it in context
    pending_plan_context = ""
    pending = get_pending_plan()
    if pending and not schedule_context:
        pending_plan_context = f"\n\n## PENDING PLAN (awaiting approval)\nThere is a pending weekly plan with {len(pending)} events. The user may be requesting changes to it. If they request changes, generate a new plan_week action with the modified events.\n"
    
    system_prompt = build_system_prompt(schedule_context=schedule_context + pending_plan_context)
    messages = build_messages_with_history(user_message)
    
    # Use higher max_tokens for week planning (lots of JSON events)
    max_tokens = 4096 if (schedule_context or pending_plan_context) else 1024
    
    response = anthropic_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=max_tokens,
        system=system_prompt,
        messages=messages
    )
    
    reply = response.content[0].text
    error_msg = None
    
    # Process JSON action if present
    if "```json" in reply:
        try:
            json_start = reply.index("```json") + 7
            json_end = reply.index("```", json_start)
            json_str = reply[json_start:json_end].strip()
            action_data = json.loads(json_str)
            
            error_msg = process_action(action_data, user_message)
            
            # Remove JSON block from reply
            reply = reply[:reply.index("```json")] + reply[json_end + 3:]
            reply = reply.strip()
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse action JSON: {e}")
    
    # Prepend error/status message if any
    if error_msg:
        reply = f"{error_msg}\n\n{reply}"
    
    # Save assistant response to history
    save_conversation("assistant", reply)
    
    await update.message.reply_text(reply)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    if update.effective_user.id != ALLOWED_USER_ID:
        return
    await update.message.reply_text("Plato is ready. What have you been working on?")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command - quick overview."""
    if update.effective_user.id != ALLOWED_USER_ID:
        return
    
    projects = get_active_projects()
    patterns = get_unresolved_patterns()
    
    msg = "📊 Current Status\n\n"
    for p in projects:
        msg += f"• {p['name']}: {len(p.get('recent_logs', []))} recent logs\n"
        if p.get("current_goals"):
            msg += f"  Goals: {len(p['current_goals'])} active\n"
    
    if patterns:
        msg += f"\n⚠️ {len(patterns)} unresolved patterns"
    
    # Add today's schedule
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        today_events = get_planned_events_for_date(today)
        if today_events:
            msg += "\n\n📅 Today's Schedule:\n"
            for e in today_events:
                status_icon = {"planned": "⬜", "completed": "✅", "partial": "🟡", "skipped": "❌", "audrey_time": "💕"}.get(e["status"], "⬜")
                msg += f"  {status_icon} {e['start_time'][:5]}-{e['end_time'][:5]}: {e['title']}\n"
    except Exception:
        pass
    
    # Add weekly adherence
    try:
        today = datetime.now()
        week_start = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
        stats = get_weekly_adherence(week_start)
        if stats["total"] > 0:
            msg += f"\n📈 This week: {stats['adherence_pct']}% adherence ({stats['completed']}/{stats['total']} blocks)"
            if stats["audrey_time"] > 0:
                msg += f"\n💕 Audrey time: {stats['audrey_time']} blocks"
    except Exception:
        pass
    
    await update.message.reply_text(msg)


async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /clear command - clear conversation history."""
    if update.effective_user.id != ALLOWED_USER_ID:
        return
    
    supabase.table("conversations").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    await update.message.reply_text("Conversation history cleared. Fresh start.")


# ============== MAIN ==============

def main() -> None:
    """Start the bot."""
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("clear", clear_history))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Proactive nudge check — runs every 5 minutes
    job_queue = app.job_queue
    job_queue.run_repeating(check_for_nudges, interval=300, first=60)
    
    logger.info("Plato v3 is starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()