import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from supabase import create_client, Client
from anthropic import Anthropic

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


def add_pattern(pattern_type: str, description: str, project_id: str | None = None) -> dict:
    """Create a new pattern entry."""
    entry = {
        "pattern_type": pattern_type,
        "description": description,
        "project_id": project_id
    }
    result = supabase.table("patterns").insert(entry).execute()
    return result.data[0]


# ============== CONTEXT ASSEMBLY ==============

def build_system_prompt() -> str:
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
When Jason messages you, determine the intent:
1. LOGGING WORK - He's reporting what he did. Extract: project (slug), summary, duration, blockers, tags, mood. Respond with the log confirmation AND perspective on progress.
2. SEEKING ADVICE - He wants to discuss something. Use Soul Doc to ground your response.
3. NEW IMPULSE - He's proposing something new. Challenge it against his existing commitments.
4. CHECK-IN - He's asking where he stands. Summarise progress honestly.
5. CREATE PROJECT - He wants to add a new project. Extract name, slug, and intent.

When logging work, respond with valid JSON in this format, followed by your message:
```json
{{"action": "log", "project_slug": "...", "summary": "...", "duration_mins": null, "blockers": null, "tags": [], "mood": null}}
```

When creating a project, respond with valid JSON in this format, followed by your message:
```json
{{"action": "create_project", "name": "...", "slug": "...", "intent": "..."}}
```

Available tags: coding, marketing, research, design, admin, learning, outreach
Available moods: energised, neutral, drained, frustrated, flow

If you detect a pattern (3+ similar blockers, repeated misses), note it.

Current date: {datetime.now().strftime("%Y-%m-%d")}
"""


# ============== MESSAGE HANDLING ==============

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages."""
    user_id = update.effective_user.id
    
    if user_id != ALLOWED_USER_ID:
        await update.message.reply_text("Plato serves only one master.")
        return
    
    user_message = update.message.text
    logger.info(f"Received: {user_message}")
    
    system_prompt = build_system_prompt()
    
    response = anthropic.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_message}
        ]
    )
    
    reply = response.content[0].text
    
    if "```json" in reply:
        try:
            json_start = reply.index("```json") + 7
            json_end = reply.index("```", json_start)
            json_str = reply[json_start:json_end].strip()
            action_data = json.loads(json_str)
            
            if action_data.get("action") == "log":
                project = get_project_by_slug(action_data["project_slug"])
                if project:
                    log_work(
                        project_id=project["id"],
                        summary=action_data["summary"],
                        duration_mins=action_data.get("duration_mins"),
                        blockers=action_data.get("blockers"),
                        tags=action_data.get("tags", []),
                        mood=action_data.get("mood"),
                        raw_message=user_message
                    )
                    logger.info(f"Logged work for {action_data['project_slug']}")
            
            elif action_data.get("action") == "create_project":
                create_project(
                    name=action_data["name"],
                    slug=action_data["slug"],
                    intent=action_data["intent"]
                )
                logger.info(f"Created project: {action_data['slug']}")
            
            reply = reply[:reply.index("```json")] + reply[json_end + 3:]
            reply = reply.strip()
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse action JSON: {e}")
    
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
        msg += f"• {p['name']}: {len(p.get('recent_logs', []))} logs this week\n"
    
    if patterns:
        msg += f"\n⚠️ {len(patterns)} unresolved patterns"
    
    await update.message.reply_text(msg)


# ============== MAIN ==============

def main() -> None:
    """Start the bot."""
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Plato is starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()