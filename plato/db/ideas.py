from datetime import datetime, timedelta
from plato.config import supabase


def park_idea(idea: str, context: str = None) -> dict:
    """Park an idea for later evaluation."""
    eligible = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    entry = {
        "idea": idea,
        "context": context,
        "eligible_date": eligible,
        "status": "parked"
    }
    result = supabase.table("idea_parking_lot").insert(entry).execute()
    return result.data[0]


def get_parked_ideas() -> list[dict]:
    """Fetch all currently parked ideas."""
    result = supabase.table("idea_parking_lot").select("*").eq("status", "parked").order("parked_at", desc=True).execute()
    return result.data


def resolve_idea(idea_fragment: str, status: str, notes: str = None) -> bool:
    """Resolve a parked idea by matching partial text."""
    ideas = get_parked_ideas()
    for idea in ideas:
        if idea_fragment.lower() in idea["idea"].lower():
            supabase.table("idea_parking_lot").update({
                "status": status,
                "resolution_notes": notes,
                "resolved_at": datetime.now().isoformat()
            }).eq("id", idea["id"]).execute()
            return True
    return False