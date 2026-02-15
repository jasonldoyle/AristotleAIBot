"""
Schedule domain — weekly planning, calendar events, check-ins.
"""


def get_action_schemas() -> str:
    return """
### SCHEDULE ACTIONS:

**PLAN WEEK** - He wants his week scheduled on Google Calendar
```json
{"action": "plan_week", "events": [
    {"date": "YYYY-MM-DD", "start": "HH:MM", "end": "HH:MM", "title": "Short descriptive title", "description": "Optional detail", "category": "nitrogen|glowbook|plato|leetcode|rest|exercise|personal|citco|audrey"}
]}
```
When planning a week, generate a COMPLETE schedule filling all free blocks. Be specific with titles.
Priorities: Side projects 8-10 hrs/week, exercise 3+ sessions, rest every evening, Sunday evening light.

### JASON'S FIXED SCHEDULE:
Mon/Tue/Fri: Wake 8:00 → Citco 9:00-18:00 → Free evening → Bed 23:00
Wed/Thu: Wake 7:30 → Travel 8:00-9:00 → Citco 9:00-18:00 → Travel 18:00-19:30 → Free evening → Bed 23:00
Saturday: Wake flexible → 9:30-10:00 drive Mam → 10:00-10:30 drive to collect groceries → 11:30 home → Free afternoon/evening
Sunday: Wake flexible → 9:00-9:30 drive Mam → 9:30-10:10 drive home → Free rest of day

Training slots: Mon (Push), Tue (Legs), Thu (Upper), Sat (Shoulders+Arms) — fit around the above.
Wed/Thu have ~1.5hr less free time due to commute.

**AUDREY TIME** - Taking the evening for girlfriend time
```json
{"action": "audrey_time", "date": "YYYY-MM-DD", "from_time": "HH:MM"}
```

**ADD ONE-OFF EVENT** - Schedule a specific event
```json
{"action": "add_event", "date": "YYYY-MM-DD", "start": "HH:MM", "end": "HH:MM", "title": "...", "category": "personal", "description": null}
```

**CHECK IN** - Record what actually happened during a planned block
```json
{"action": "check_in", "event_id": "uuid-or-null", "status": "completed|partial|skipped", "actual_summary": "What actually got done", "gap_reason": "Why it didn't go to plan (if partial/skipped)"}
```"""


def get_context() -> str:
    """Schedule context is handled by the always-on today_schedule_brief."""
    return ""
