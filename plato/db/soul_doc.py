from plato.config import supabase


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


def add_soul_doc_entry(content: str, category: str, trigger: str) -> dict:
    """Add a new soul doc entry."""
    entry = {
        "content": content,
        "category": category,
        "trigger": trigger
    }
    result = supabase.table("soul_doc").insert(entry).execute()
    return result.data[0]