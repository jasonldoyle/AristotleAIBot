from plato.config import supabase


def get_recent_conversations(limit: int = 10) -> list[dict]:
    """Fetch recent conversation history."""
    result = supabase.table("conversations").select("*").order("created_at", desc=True).limit(limit).execute()
    return list(reversed(result.data)) if result.data else []


def save_conversation(role: str, content: str) -> None:
    """Save a message to conversation history."""
    supabase.table("conversations").insert({"role": role, "content": content}).execute()


def clear_conversations() -> None:
    """Delete all conversation history."""
    supabase.table("conversations").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()