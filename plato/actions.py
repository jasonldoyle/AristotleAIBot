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

            case _:
                logger.warning(f"Unknown action type: {action_type}")
                return f"Unknown action: {action_type}"

    except Exception as e:
        logger.error(f"Action '{action_type}' failed: {e}")
        return f"Action failed: {e}"
