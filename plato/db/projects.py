from datetime import datetime
from plato.config import supabase


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


def log_work(project_id: str, summary: str, duration_mins: int | None,
             blockers: str | None, tags: list[str], mood: str | None,
             raw_message: str) -> dict:
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


def add_project_goal(project_id: str, timeframe: str, goal_text: str,
                     target_date: str | None = None) -> dict:
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


def add_pattern(pattern_type: str, description: str,
                project_id: str | None = None) -> dict:
    """Create a new pattern entry."""
    entry = {
        "pattern_type": pattern_type,
        "description": description,
        "project_id": project_id
    }
    result = supabase.table("patterns").insert(entry).execute()
    return result.data[0]