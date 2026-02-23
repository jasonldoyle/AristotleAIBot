from plato.config import logger
from plato.db import (
    add_soul_entry,
    update_soul_entry,
    get_soul_doc,
    format_soul_doc,
    store_idea,
    park_idea,
    get_ideas,
    format_ideas,
    resolve_idea,
    create_project,
    get_projects,
    get_project_by_slug,
    update_project_status,
    add_project_goal,
    achieve_goal,
    log_work,
    get_project_summary,
    format_projects_summary,
    format_project_detail,
)


def process_action(action: dict) -> str:
    """Route a JSON action block from Claude and return a status message."""
    action_type = action.get("action")
    try:
        match action_type:
            case "add_soul":
                entry_id = add_soul_entry(action["category"], action["content"])
                return f"Soul doc entry added ({action['category']})."

            case "update_soul":
                entry_id = update_soul_entry(action["category"], action["old_content"], action["content"])
                return f"Soul doc entry updated ({action['category']})."

            case "store_idea":
                idea_id = store_idea(action["idea"], action.get("context"))
                return f"Idea stored."

            case "park_idea":
                found = park_idea(action["idea_id"])
                if found:
                    return "Idea parked. 14-day cooling period started."
                return "Idea not found."

            case "resolve_idea":
                found = resolve_idea(action["idea_id"], action["status"], action.get("notes"))
                if found:
                    return f"Idea {action['status']}."
                return "Idea not found."

            case "query_soul":
                grouped = get_soul_doc()
                return format_soul_doc(grouped)

            case "query_ideas":
                ideas = get_ideas()
                return format_ideas(ideas)

            case "create_project":
                project_id = create_project(action["name"], action["slug"], action.get("intent"))
                return f"Project '{action['name']}' created (slug: {action['slug']})."

            case "log_work":
                project = get_project_by_slug(action["slug"])
                if not project:
                    return f"Project '{action['slug']}' not found."
                log_work(project["id"], action["summary"], action.get("duration_mins"), action.get("mood"))
                return f"Work logged on {project['name']}."

            case "add_goal":
                project = get_project_by_slug(action["slug"])
                if not project:
                    return f"Project '{action['slug']}' not found."
                add_project_goal(project["id"], action["timeframe"], action["goal_text"], action.get("target_date"))
                return f"Goal added to {project['name']} ({action['timeframe']})."

            case "achieve_goal":
                found = achieve_goal(action["goal_id"])
                if found:
                    return "Goal achieved! Well done."
                return "Goal not found."

            case "update_project":
                project = get_project_by_slug(action["slug"])
                if not project:
                    return f"Project '{action['slug']}' not found."
                update_project_status(project["id"], action["status"])
                return f"Project '{project['name']}' status updated to {action['status']}."

            case "query_projects":
                projects = get_projects(status="active")
                return format_projects_summary(projects)

            case "query_project":
                summary = get_project_summary(action["slug"])
                return format_project_detail(summary)

            case _:
                logger.warning(f"Unknown action type: {action_type}")
                return f"Unknown action: {action_type}"

    except Exception as e:
        logger.error(f"Action '{action_type}' failed: {e}")
        return f"Action failed: {e}"
