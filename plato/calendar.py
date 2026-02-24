"""
Plato Calendar Module — Google Calendar integration for weekly planning.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

COLOR_MAP = {
    "cfa": "9",        # Blueberry
    "nitrogen": "10",  # Basil
    "glowbook": "6",   # Tangerine
    "plato": "7",      # Peacock
    "leetcode": "3",   # Grape
    "rest": "8",       # Graphite
    "exercise": "2",   # Sage
    "personal": "4",   # Flamingo
    "citco": "1",      # Lavender
    "audrey": "11",    # Tomato
}


def get_calendar_service():
    """Build Google Calendar service from env var credentials."""
    refresh_token = os.environ.get("GOOGLE_REFRESH_TOKEN")
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")

    if not all([refresh_token, client_id, client_secret]):
        missing = [k for k, v in {
            "GOOGLE_REFRESH_TOKEN": refresh_token,
            "GOOGLE_CLIENT_ID": client_id,
            "GOOGLE_CLIENT_SECRET": client_secret,
        }.items() if not v]
        raise ValueError(f"Missing Google Calendar credentials: {missing}")

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        token_uri="https://oauth2.googleapis.com/token"
    )
    service = build('calendar', 'v3', credentials=creds)
    logger.info("Google Calendar service built successfully")
    return service


def get_weekly_template(week_start: datetime) -> dict:
    """
    Returns Jason's weekly availability template.
    week_start should be a Monday.

    Post-cutover (March 1 2026): Office Tue, Wed, Thu
    Gym: Mon, Tue 18:00-19:40 | Fri 18:00-19:40 | Sat 07:30-09:00
    Mam driving: Sat 09:15-10:45 + 19:00-20:30, Sun 09:00-10:30 + 19:00-20:30
    Groceries: Sat 10:45-11:15
    """
    office_days = [1, 2, 3]  # Tue, Wed, Thu (0-indexed from Mon)
    gym_weekdays = [0, 1, 4]  # Mon, Tue, Fri

    template = {
        "week_start": week_start.strftime("%Y-%m-%d"),
        "days": []
    }

    for day_offset in range(7):
        current_date = week_start + timedelta(days=day_offset)
        day_name = current_date.strftime("%A")

        if day_offset < 5:  # Weekday
            is_office = day_offset in office_days
            is_gym_day = day_offset in gym_weekdays

            if is_office and is_gym_day:
                blocks = [
                    {"start": "07:30", "end": "08:00", "type": "commute_prep", "label": "Get ready, lift to Luas"},
                    {"start": "08:00", "end": "09:00", "type": "commute", "label": "Luas to Citco"},
                    {"start": "09:00", "end": "18:00", "type": "work", "label": "Citco (Office)"},
                    {"start": "18:00", "end": "19:30", "type": "commute", "label": "Walk > Luas > Walk home"},
                    {"start": "19:30", "end": "19:45", "type": "commute", "label": "Travel to gym"},
                    {"start": "19:45", "end": "20:50", "type": "fixed", "label": "Gym session"},
                    {"start": "20:50", "end": "21:10", "type": "commute", "label": "Travel home from gym"},
                    {"start": "21:10", "end": "23:00", "type": "free", "label": "Evening block (1.8 hrs)"},
                ]
            elif is_office:
                blocks = [
                    {"start": "07:30", "end": "08:00", "type": "commute_prep", "label": "Get ready, lift to Luas"},
                    {"start": "08:00", "end": "09:00", "type": "commute", "label": "Luas to Citco"},
                    {"start": "09:00", "end": "18:00", "type": "work", "label": "Citco (Office)"},
                    {"start": "18:00", "end": "19:30", "type": "commute", "label": "Walk > Luas > Walk home"},
                    {"start": "19:30", "end": "23:00", "type": "free", "label": "Evening block (3.5 hrs)"},
                ]
            else:
                if is_gym_day:
                    blocks = [
                        {"start": "07:30", "end": "09:00", "type": "free", "label": "Morning block (1.5 hrs)"},
                        {"start": "09:00", "end": "18:00", "type": "work", "label": "Citco (WFH)"},
                        {"start": "18:00", "end": "18:15", "type": "commute", "label": "Travel to gym"},
                        {"start": "18:15", "end": "19:20", "type": "fixed", "label": "Gym session"},
                        {"start": "19:20", "end": "19:40", "type": "commute", "label": "Travel home from gym"},
                        {"start": "19:40", "end": "23:00", "type": "free", "label": "Evening block (3.3 hrs)"},
                    ]
                else:
                    blocks = [
                        {"start": "07:30", "end": "09:00", "type": "free", "label": "Morning block (1.5 hrs)"},
                        {"start": "09:00", "end": "18:00", "type": "work", "label": "Citco (WFH)"},
                        {"start": "18:00", "end": "23:00", "type": "free", "label": "Evening block (5 hrs)"},
                    ]

            template["days"].append({
                "date": current_date.strftime("%Y-%m-%d"),
                "day": day_name,
                "location": "office" if is_office else "wfh",
                "blocks": blocks
            })

        else:  # Weekend
            if day_offset == 5:  # Saturday
                blocks = [
                    {"start": "07:30", "end": "09:00", "type": "fixed", "label": "Gym session"},
                    {"start": "09:15", "end": "10:45", "type": "fixed", "label": "Drive mam to guzheng school"},
                    {"start": "10:45", "end": "11:15", "type": "fixed", "label": "Click & collect groceries"},
                    {"start": "11:15", "end": "19:00", "type": "free", "label": "Main block (7.75 hrs)"},
                    {"start": "19:00", "end": "20:30", "type": "fixed", "label": "Pick up mam from guzheng"},
                    {"start": "20:30", "end": "23:00", "type": "free", "label": "Evening block (2.5 hrs)"},
                ]
            else:  # Sunday
                blocks = [
                    {"start": "07:30", "end": "09:00", "type": "free", "label": "Early morning (1.5 hrs)"},
                    {"start": "09:00", "end": "10:30", "type": "fixed", "label": "Drive mam to guzheng school"},
                    {"start": "10:30", "end": "19:00", "type": "free", "label": "Main block (8.5 hrs)"},
                    {"start": "19:00", "end": "20:30", "type": "fixed", "label": "Pick up mam from guzheng"},
                    {"start": "20:30", "end": "23:00", "type": "free", "label": "Evening block (2.5 hrs — keep light)"},
                ]

            template["days"].append({
                "date": current_date.strftime("%Y-%m-%d"),
                "day": day_name,
                "location": "home",
                "blocks": blocks
            })

    return template


def clear_plato_events(service, week_start: datetime):
    """Remove all [Plato]-prefixed events for the given week."""
    week_end = week_start + timedelta(days=7)

    events_result = service.events().list(
        calendarId='primary',
        timeMin=week_start.strftime("%Y-%m-%d") + 'T00:00:00Z',
        timeMax=week_end.strftime("%Y-%m-%d") + 'T00:00:00Z',
        singleEvents=True,
        q='[Plato]'
    ).execute()

    events = events_result.get('items', [])
    deleted = 0
    for event in events:
        if '[Plato]' in event.get('summary', ''):
            service.events().delete(calendarId='primary', eventId=event['id']).execute()
            deleted += 1

    logger.info(f"Cleared {deleted} existing Plato events")
    return deleted


def cancel_evening_events(service, date_str: str, from_time: str = "18:00"):
    """Cancel [Plato] events for a specific evening. Returns list of cancelled titles."""
    cancelled = []

    events_result = service.events().list(
        calendarId='primary',
        timeMin=f'{date_str}T{from_time}:00',
        timeMax=f'{date_str}T23:59:00',
        timeZone='Europe/Dublin',
        singleEvents=True,
        q='[Plato]'
    ).execute()

    for event in events_result.get('items', []):
        if '[Plato]' in event.get('summary', ''):
            title = event['summary'].replace('[Plato] ', '')
            service.events().delete(calendarId='primary', eventId=event['id']).execute()
            cancelled.append(title)

    return cancelled


def cancel_specific_event(service, date_str: str, title_keyword: str):
    """Cancel a specific [Plato] event matching date + title keyword. Returns cancelled title or None."""
    events_result = service.events().list(
        calendarId='primary',
        timeMin=f'{date_str}T00:00:00',
        timeMax=f'{date_str}T23:59:00',
        timeZone='Europe/Dublin',
        singleEvents=True,
        q='[Plato]'
    ).execute()

    for event in events_result.get('items', []):
        summary = event.get('summary', '')
        if '[Plato]' in summary and title_keyword.lower() in summary.lower():
            service.events().delete(calendarId='primary', eventId=event['id']).execute()
            return summary.replace('[Plato] ', '')
    return None


def create_event(service, date_str: str, start_time: str, end_time: str,
                 title: str, description: str = None, color_id: str = None):
    """Create a single Google Calendar event in Europe/Dublin timezone."""
    event = {
        'summary': f'[Plato] {title}',
        'start': {
            'dateTime': f'{date_str}T{start_time}:00',
            'timeZone': 'Europe/Dublin',
        },
        'end': {
            'dateTime': f'{date_str}T{end_time}:00',
            'timeZone': 'Europe/Dublin',
        },
    }

    if description:
        event['description'] = description
    if color_id:
        event['colorId'] = color_id

    created = service.events().insert(calendarId='primary', body=event).execute()
    logger.info(f"Created event: '{title}' on {date_str} {start_time}-{end_time}")
    return created


def create_weekly_events(service, schedule_events: list) -> int:
    """Create all events from a planned schedule. Returns count of created events."""
    created_count = 0
    for event in schedule_events:
        try:
            color = COLOR_MAP.get(event.get("category", ""))
            create_event(
                service,
                date_str=event["date"],
                start_time=event["start"],
                end_time=event["end"],
                title=event["title"],
                description=event.get("description"),
                color_id=color
            )
            created_count += 1
        except Exception as e:
            logger.error(f"Failed to create event '{event.get('title')}': {e}")

    return created_count


def get_schedule_prompt(week_start: datetime, active_projects: list[dict] = None) -> str:
    """Build scheduling context string with template + rules for Claude."""
    template = get_weekly_template(week_start)

    # Build dynamic project allocation rules
    if active_projects:
        project_lines = []
        slugs = []
        for p in active_projects:
            slugs.append(p["slug"])
            project_lines.append(f"  - **{p['name']}** (slug: {p['slug']})" + (f" — {p['intent']}" if p.get('intent') else ""))
        project_section = "Active projects to schedule:\n" + "\n".join(project_lines)
        category_list = "|".join(slugs) + "|rest|exercise|personal"
    else:
        project_section = "No active projects. Schedule rest and personal time."
        category_list = "rest|exercise|personal"

    return f"""
## WEEKLY SCHEDULE PLANNING

You are planning Jason's week starting {week_start.strftime('%A %B %d, %Y')}.

### Weekly Template
The template below shows Jason's fixed commitments and free blocks. You MUST respect these constraints.
{json.dumps(template, indent=2)}

### {project_section}

Distribute project time across the week based on their goals and priorities from the soul doc.

### Scheduling Rules
1. NEVER schedule over "work", "commute", "commute_prep", or "fixed" blocks — these are non-negotiable
2. Only fill "free" blocks with project work, rest, or personal time
3. Prioritise projects based on soul doc goals and upcoming deadlines
4. Rest/downtime — at least 1 hour every evening, one long rest block on weekend
5. Exercise — gym sessions (Mon, Tue, Fri evenings + Sat morning) are already fixed in the template, do NOT add separate exercise events for those
6. Keep Sunday evening light — wind down for the work week
7. Batch similar work: don't alternate between different projects in the same evening
8. Morning WFH blocks (07:30-09:00) are good for focused study — fresh mind, no distractions
9. Audrey time may be declared spontaneously — leave some buffer, don't over-optimise
10. Office days (Tue/Wed/Thu): only the evening post-commute block is free
11. WFH days (Mon/Fri): morning block + evening block are free

### Response Format
Return a plan_week action with an "events" array. Each event:
```
{{
    "date": "YYYY-MM-DD",
    "start": "HH:MM",
    "end": "HH:MM",
    "title": "Short descriptive title",
    "description": "Optional detail or focus area",
    "category": "{category_list}|citco|exercise"
}}
```

IMPORTANT: Include EVERY block for ALL 7 days (Monday through Sunday) in the events array — this builds a COMPLETE calendar for the week:
- Work blocks (category: "citco") — e.g. "Citco (Office)" or "Citco (WFH)"
- Commute blocks (category: "citco") — e.g. "Commute to office", "Commute home"
- Gym sessions (category: "exercise") — from the template's fixed blocks
- Mam driving (category: "personal") — from the template's fixed blocks
- Groceries (category: "personal") — from the template
- Project work, rest, personal time — filling the free blocks

The calendar should show Jason's ENTIRE day, not just the free blocks you filled in.
Be specific with project titles: "Plato - Phase 3 testing" not just "Plato".
Only schedule projects that are listed above as active. Do NOT invent projects.
"""
