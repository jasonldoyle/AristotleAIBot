import os
import json
import logging
from datetime import datetime, timedelta
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
    create_weekly_events
)

# Config
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
ALLOWED_USER_ID = int(os.environ.get("ALLOWED_USER_ID", 0))

# Clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)

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
    """Process a plan_week action - create Google Calendar events."""
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


# ============== CONTEXT ASSEMBLY ==============

def build_system_prompt(schedule_context: str = "") -> str:
    """Build Plato's system prompt with current context."""
    soul_doc = get_soul_doc()
    projects = get_active_projects()
    patterns = get_unresolved_patterns()
    
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
    
    return f"""You are Plato, Jason's personal AI mentor. You embody stoic wisdom and hold him accountable to his long-term goals.

Your role:
- Parse work logs and store them accurately
- Provide perspective grounded in his Soul Doc (life goals)
- Call out deviations, impulses, and patterns
- Be direct, honest, and occasionally challenging
- Celebrate genuine progress, but don't flatter

## SOUL DOC (His Constitution)
{soul_doc}

## ACTIVE PROJECTS
{projects_context}
{patterns_context}

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
    {{"date": "YYYY-MM-DD", "start": "HH:MM", "end": "HH:MM", "title": "Short descriptive title", "description": "Optional detail", "category": "cfa|nitrogen|glowbook|plato|leetcode|rest|exercise|personal|citco"}}
]}}
```
When planning a week, generate a COMPLETE schedule filling all free blocks. Be specific with titles (e.g. "CFA - Ethics Chapter 3" not just "CFA Study").
Priorities: CFA study minimum 10 hrs/week, side projects 8-10 hrs/week, exercise 3+ sessions, rest every evening, Sunday evening light.

### GUIDELINES:
- Available tags: coding, marketing, research, design, admin, learning, outreach
- Available moods: energised, neutral, drained, frustrated, flow
- If no action is needed (just conversation), don't include a JSON block
- Always provide your mentorship response AFTER the JSON block
- Be concise but insightful
- If he's going off-track, call it out firmly but kindly

Current date: {datetime.now().strftime("%Y-%m-%d")}
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
    
    # Check if planning week — add schedule context if so
    schedule_context = detect_plan_week(user_message) or ""
    
    system_prompt = build_system_prompt(schedule_context=schedule_context)
    messages = build_messages_with_history(user_message)
    
    # Use higher max_tokens for week planning (lots of JSON events)
    max_tokens = 4096 if schedule_context else 1024
    
    response = anthropic.messages.create(
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
    
    msg = "**Current Status**\n\n"
    for p in projects:
        msg += f"• {p['name']}: {len(p.get('recent_logs', []))} recent logs\n"
        if p.get("current_goals"):
            msg += f"  Goals: {len(p['current_goals'])} active\n"
    
    if patterns:
        msg += f"\n⚠️ {len(patterns)} unresolved patterns"
    
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
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("clear", clear_history))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Plato is starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()