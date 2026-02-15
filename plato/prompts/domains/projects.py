"""
Projects domain — work logging, goals, patterns, project management.
"""

from plato.db import get_active_projects, get_unresolved_patterns


def get_action_schemas() -> str:
    return """
### PROJECT ACTIONS:

**LOG WORK** - He's reporting what he did
```json
{"action": "log", "project_slug": "...", "summary": "...", "duration_mins": null, "blockers": null, "tags": [], "mood": null}
```

**CREATE PROJECT** - He wants to add a new project
```json
{"action": "create_project", "name": "...", "slug": "...", "intent": "..."}
```

**ADD SOUL DOC** - He says "soullog:/" or wants to record a life principle/goal
```json
{"action": "add_soul", "content": "...", "category": "goal_lifetime|goal_5yr|goal_2yr|goal_1yr|philosophy|rule|anti_pattern", "trigger": "..."}
```

**SET PROJECT GOAL** - He wants to set a weekly/monthly/quarterly goal
```json
{"action": "add_goal", "project_slug": "...", "timeframe": "weekly|monthly|quarterly|milestone", "goal_text": "...", "target_date": null}
```

**MARK GOAL ACHIEVED** - He completed a goal
```json
{"action": "achieve_goal", "project_slug": "...", "goal_fragment": "..."}
```

**UPDATE PROJECT** - He wants to change project details
```json
{"action": "update_project", "slug": "...", "updates": {"target_date": null, "estimated_weekly_hours": null, "stick_twist_criteria": null, "alignment_rationale": null}}
```

**LOG PATTERN** - He's noticed a recurring behaviour
```json
{"action": "add_pattern", "pattern_type": "blocker|overestimation|external_constraint|bad_habit|avoidance", "description": "...", "project_slug": null}
```"""


def get_context() -> str:
    """Build projects context with active projects and patterns."""
    projects = get_active_projects()
    patterns = get_unresolved_patterns()

    context = ""

    if projects:
        context += "\n## ACTIVE PROJECTS\n"
        for p in projects:
            context += f"\n### {p['name']} ({p['slug']})\n"
            context += f"Intent: {p['intent']}\n"
            context += f"Target: {p.get('target_date', 'No deadline')}\n"
            context += f"Weekly hours allocated: {p.get('estimated_weekly_hours', 'Not set')}\n"
            context += f"Stick/Twist: {p.get('stick_twist_criteria', 'Not defined')}\n"

            if p.get("current_goals"):
                context += "Current goals:\n"
                for g in p["current_goals"]:
                    context += f"  - [{g['timeframe']}] {g['goal_text']}\n"

            if p.get("recent_logs"):
                context += "Recent activity:\n"
                for log in p["recent_logs"][:3]:
                    context += f"  - {log['logged_at'][:10]}: {log['summary']}\n"

    if patterns:
        context += "\n## UNRESOLVED PATTERNS\n"
        for pat in patterns:
            context += f"- [{pat['pattern_type']}] {pat['description']} (seen {pat['occurrence_count']}x)\n"

    return context
