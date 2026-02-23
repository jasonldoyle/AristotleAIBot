from datetime import datetime, timezone

from plato.config import SessionLocal
from plato.models import Project, ProjectGoal, ProjectLog


def create_project(name: str, slug: str, intent: str = None) -> str:
    """Create a new project. Returns the project ID."""
    with SessionLocal() as session:
        project = Project(name=name, slug=slug, intent=intent, status="active")
        session.add(project)
        session.commit()
        return str(project.id)


def get_projects(status: str = None) -> list[dict]:
    """Fetch projects, optionally filtered by status."""
    with SessionLocal() as session:
        query = session.query(Project).order_by(Project.created_at)
        if status:
            query = query.filter(Project.status == status)
        rows = query.all()
        return [
            {
                "id": str(r.id),
                "name": r.name,
                "slug": r.slug,
                "intent": r.intent,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]


def _to_dict(r) -> dict:
    return {
        "id": str(r.id),
        "name": r.name,
        "slug": r.slug,
        "intent": r.intent,
        "status": r.status,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def get_project_by_slug(slug: str) -> dict | None:
    """Fetch a single project by slug. Tries exact match, then normalized fuzzy match."""
    normalized = slug.lower().replace("-", "").replace("_", "").replace(" ", "")
    with SessionLocal() as session:
        # Exact match first
        r = session.query(Project).filter_by(slug=slug).first()
        if r:
            return _to_dict(r)
        # Fuzzy: normalize and try contains/startswith
        all_projects = session.query(Project).all()
        for r in all_projects:
            stored = r.slug.lower().replace("-", "").replace("_", "").replace(" ", "")
            if stored == normalized or normalized.startswith(stored) or stored.startswith(normalized):
                return _to_dict(r)
        return None


def update_project_status(project_id: str, status: str) -> bool:
    """Update a project's status. Returns True if found."""
    valid = ("active", "paused", "completed", "abandoned")
    if status not in valid:
        raise ValueError(f"Invalid status: {status}. Must be one of {valid}")
    with SessionLocal() as session:
        project = session.query(Project).filter_by(id=project_id).first()
        if not project:
            return False
        project.status = status
        session.commit()
        return True


def add_project_goal(project_id: str, timeframe: str, goal_text: str, target_date: str = None) -> str:
    """Add a goal to a project. Returns the goal ID."""
    valid = ("weekly", "monthly", "quarterly", "milestone")
    if timeframe not in valid:
        raise ValueError(f"Invalid timeframe: {timeframe}. Must be one of {valid}")
    with SessionLocal() as session:
        goal = ProjectGoal(
            project_id=project_id,
            timeframe=timeframe,
            goal_text=goal_text,
            target_date=datetime.fromisoformat(target_date) if target_date else None,
        )
        session.add(goal)
        session.commit()
        return str(goal.id)


def achieve_goal(goal_id: str) -> bool:
    """Mark a goal as achieved. Returns True if found."""
    with SessionLocal() as session:
        goal = session.query(ProjectGoal).filter_by(id=goal_id).first()
        if not goal:
            return False
        goal.achieved = True
        goal.achieved_at = datetime.now(timezone.utc)
        session.commit()
        return True


def get_project_goals(project_id: str) -> list[dict]:
    """Fetch goals for a project."""
    with SessionLocal() as session:
        rows = (
            session.query(ProjectGoal)
            .filter_by(project_id=project_id)
            .order_by(ProjectGoal.created_at)
            .all()
        )
        return [
            {
                "id": str(r.id),
                "timeframe": r.timeframe,
                "goal_text": r.goal_text,
                "target_date": r.target_date.isoformat() if r.target_date else None,
                "achieved": r.achieved,
                "achieved_at": r.achieved_at.isoformat() if r.achieved_at else None,
            }
            for r in rows
        ]


def log_work(project_id: str, summary: str, duration_mins: int = None, mood: str = None) -> str:
    """Log a work session. Returns the log ID."""
    with SessionLocal() as session:
        log = ProjectLog(
            project_id=project_id,
            summary=summary,
            duration_mins=duration_mins,
            mood=mood,
        )
        session.add(log)
        session.commit()
        return str(log.id)


def get_project_logs(project_id: str, limit: int = 10) -> list[dict]:
    """Fetch recent work logs for a project."""
    with SessionLocal() as session:
        rows = (
            session.query(ProjectLog)
            .filter_by(project_id=project_id)
            .order_by(ProjectLog.logged_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": str(r.id),
                "summary": r.summary,
                "duration_mins": r.duration_mins,
                "mood": r.mood,
                "logged_at": r.logged_at.isoformat() if r.logged_at else None,
            }
            for r in rows
        ]


def get_project_summary(slug: str) -> dict | None:
    """Get a project with its active goals and recent logs."""
    project = get_project_by_slug(slug)
    if not project:
        return None
    project["goals"] = get_project_goals(project["id"])
    project["recent_logs"] = get_project_logs(project["id"], limit=5)
    return project


def format_projects_summary(projects: list[dict]) -> str:
    """Format active projects with goals for the system prompt."""
    if not projects:
        return "No active projects."

    parts = []
    for p in projects:
        line = f"**{p['name']}** (slug: {p['slug']}) [{p['status']}]"
        if p.get("intent"):
            line += f" — {p['intent']}"
        parts.append(line)

        goals = get_project_goals(p["id"])
        active_goals = [g for g in goals if not g["achieved"]]
        if active_goals:
            for g in active_goals:
                parts.append(f"  - [{g['timeframe']}] {g['goal_text']}")

        logs = get_project_logs(p["id"], limit=1)
        if logs:
            parts.append(f"  Last log: {logs[0]['logged_at'][:10]}")

    return "\n".join(parts)


def format_project_detail(summary: dict) -> str:
    """Format a single project summary for display."""
    if not summary:
        return "Project not found."

    parts = [f"**{summary['name']}** [{summary['status']}]"]
    if summary.get("intent"):
        parts.append(f"Intent: {summary['intent']}")

    goals = summary.get("goals", [])
    if goals:
        parts.append("\nGoals:")
        for g in goals:
            status = "ACHIEVED" if g["achieved"] else g["timeframe"]
            parts.append(f"  - [{status}] {g['goal_text']}")
            if g["achieved"] and g["achieved_at"]:
                parts.append(f"    Achieved: {g['achieved_at'][:10]}")
            if not g["achieved"]:
                parts.append(f"    ID: {g['id'][:8]}...")

    logs = summary.get("recent_logs", [])
    if logs:
        parts.append("\nRecent work:")
        for l in logs:
            entry = f"  - {l['logged_at'][:10]}: {l['summary']}"
            if l.get("duration_mins"):
                entry += f" ({l['duration_mins']}min)"
            if l.get("mood"):
                entry += f" [{l['mood']}]"
            parts.append(entry)

    return "\n".join(parts)
