"""
Ideas domain — idea parking lot.
"""

from datetime import datetime
from plato.db import get_parked_ideas


def get_action_schemas() -> str:
    return """
### IDEA ACTIONS:

**PARK IDEA** - New project/idea not aligned with current commitments
```json
{"action": "park_idea", "idea": "Short description", "context": "Why it came up"}
```

**RESOLVE IDEA** - Approve or reject a parked idea after cooling period
```json
{"action": "resolve_idea", "idea_fragment": "partial match text", "status": "approved|rejected", "notes": "Why"}
```"""


def get_context() -> str:
    """Build ideas context with parked ideas."""
    parked_ideas = get_parked_ideas()
    if not parked_ideas:
        return ""

    context = "\n## IDEA PARKING LOT\n"
    for idea in parked_ideas:
        days_left = (datetime.strptime(idea["eligible_date"], "%Y-%m-%d") - datetime.now()).days
        if days_left > 0:
            context += f"- 💡 {idea['idea']} (parked {idea['parked_at'][:10]}, {days_left} days until eligible)\n"
        else:
            context += f"- 🟢 {idea['idea']} (ELIGIBLE — parked {idea['parked_at'][:10]}, ready for review)\n"
    return context
