"""
Intent detection for routing messages to relevant domains.
Simple keyword matching — no ML needed for a single-user bot.
"""

DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "fitness": [
        "workout", "gym", "weight", "training", "block", "lift", "squat",
        "bench", "nutrition", "mfp", "skincare", "cycling", "progress photos",
        "exercise", "bulk", "cut", "protein", "calories", "incline", "ohp",
        "barbell", "dumbbell", "session", "push day", "leg day", "upper",
        "shoulders", "arms", "deload", "reps", "sets", "kg", "body fat",
        "physique", "muscle", "abs",
    ],
    "schedule": [
        "plan", "week", "schedule", "calendar", "approve", "audrey time",
        "event", "check in", "checked in", "block ended",
    ],
    "projects": [
        "project", "log", "work", "coding", "nitrogen", "glowbook", "cfa",
        "plato", "leetcode", "goal", "milestone",
    ],
    "finance": [
        "spend", "budget", "money", "finance", "revolut", "aib", "csv",
        "saving", "income", "transaction",
    ],
    "admin": [
        "task", "todo", "reminder", "birthday", "recurring", "laundry",
        "overdue", "due", "important date",
    ],
    "ideas": [
        "idea", "park", "parked",
    ],
}


def detect_domains(message: str) -> set[str]:
    """Detect which domains a message relates to based on keyword matching."""
    msg_lower = message.lower()
    detected = set()

    for domain, keywords in DOMAIN_KEYWORDS.items():
        for keyword in keywords:
            if keyword in msg_lower:
                detected.add(domain)
                break

    return detected
