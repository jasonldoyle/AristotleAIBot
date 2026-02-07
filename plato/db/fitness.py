from datetime import datetime, timedelta
from plato.config import supabase


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


def get_recent_fitness(days: int = 7) -> list[dict]:
    """Fetch fitness logs from the last N days."""
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    result = supabase.table("fitness_logs").select("*").gte("session_date", since).order("session_date", desc=True).execute()
    return result.data