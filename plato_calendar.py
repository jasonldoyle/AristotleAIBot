"""
Plato Calendar Module v3
Handles Google Calendar integration, weekly planning, and schedule tracking.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)


# ============== AUTH ==============

def get_calendar_service():
    """Build Google Calendar service from stored credentials."""
    creds = Credentials(
        token=None,
        refresh_token=os.environ.get("GOOGLE_REFRESH_TOKEN"),
        client_id=os.environ.get("GOOGLE_CLIENT_ID"),
        client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
        token_uri="https://oauth2.googleapis.com/token"
    )
    return build('calendar', 'v3', credentials=creds)


# ============== WEEKLY TEMPLATE ==============

def get_weekly_template(week_start: datetime) -> dict:
    """
    Returns Jason's weekly availability template.
    week_start should be a Monday.
    
    Until March 1st 2026: WFH Mon, Tue, Fri | Office Wed, Thu
    After March 1st 2026: WFH Mon, Fri | Office Tue, Wed, Thu
    
    Fixed commitments:
    - Gym: Mon & Tue 18:00-19:40 (travel + session)
    - Mam's guzheng: Sat & Sun 09:15-10:45 and 19:00-20:30
    - Click & collect: Saturday ~10:45-11:15 (on way home from guzheng drop-off)
    """
    
    cutover = datetime(2026, 3, 1)
    
    if week_start < cutover:
        office_days = [2, 3]  # Wed=2, Thu=3 (0-indexed from Mon)
    else:
        office_days = [1, 2, 3]  # Tue, Wed, Thu

    template = {
        "week_start": week_start.isoformat(),
        "days": []
    }
    
    for day_offset in range(7):
        current_date = week_start + timedelta(days=day_offset)
        day_name = current_date.strftime("%A")
        
        if day_offset < 5:  # Weekday
            is_office = day_offset in office_days
            is_gym_day = day_offset in [0, 1]  # Mon=0, Tue=1
            
            if is_office:
                blocks = [
                    {"start": "07:30", "end": "08:00", "type": "commute_prep", "label": "Get ready, lift to Luas"},
                    {"start": "08:00", "end": "09:00", "type": "commute", "label": "Luas to Citco"},
                    {"start": "09:00", "end": "18:00", "type": "work", "label": "Citco (Office)"},
                    {"start": "18:00", "end": "19:30", "type": "commute", "label": "Walk → Luas → Walk home"},
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
                    {"start": "07:30", "end": "09:15", "type": "free", "label": "Early morning (1.75 hrs)"},
                    {"start": "09:15", "end": "10:45", "type": "fixed", "label": "Drive mam to guzheng school"},
                    {"start": "10:45", "end": "11:15", "type": "fixed", "label": "Click & collect groceries (on way home)"},
                    {"start": "11:15", "end": "19:00", "type": "free", "label": "Main block (7.75 hrs)"},
                    {"start": "19:00", "end": "20:30", "type": "fixed", "label": "Pick up mam from guzheng"},
                    {"start": "20:30", "end": "23:00", "type": "free", "label": "Evening block (2.5 hrs)"},
                ]
            else:  # Sunday
                blocks = [
                    {"start": "07:30", "end": "09:15", "type": "free", "label": "Early morning (1.75 hrs)"},
                    {"start": "09:15", "end": "10:45", "type": "fixed", "label": "Drive mam to guzheng school"},
                    {"start": "10:45", "end": "19:00", "type": "free", "label": "Main block (8.25 hrs)"},
                    {"start": "19:00", "end": "20:30", "type": "fixed", "label": "Pick up mam from guzheng"},
                    {"start": "20:30", "end": "23:00", "type": "free", "label": "Evening block (2.5 hrs — keep light, wind down)"},
                ]
            
            template["days"].append({
                "date": current_date.strftime("%Y-%m-%d"),
                "day": day_name,
                "location": "home",
                "blocks": blocks
            })
    
    return template


# ============== CALENDAR OPERATIONS ==============

def clear_plato_events(service, week_start: datetime):
    """Remove all Plato-created events for the given week."""
    week_end = week_start + timedelta(days=7)
    
    events_result = service.events().list(
        calendarId='primary',
        timeMin=week_start.isoformat() + 'T00:00:00Z',
        timeMax=week_end.isoformat() + 'T00:00:00Z',
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
    """Cancel Plato events for a specific evening. Returns list of cancelled event titles."""
    cancelled = []
    
    events_result = service.events().list(
        calendarId='primary',
        timeMin=f'{date_str}T{from_time}:00+00:00',
        timeMax=f'{date_str}T23:59:00+00:00',
        singleEvents=True,
        q='[Plato]'
    ).execute()
    
    for event in events_result.get('items', []):
        if '[Plato]' in event.get('summary', ''):
            title = event['summary'].replace('[Plato] ', '')
            service.events().delete(calendarId='primary', eventId=event['id']).execute()
            cancelled.append({
                "title": title,
                "start": event['start'].get('dateTime', ''),
                "end": event['end'].get('dateTime', '')
            })
    
    return cancelled


def get_todays_events(service, date_str: str = None):
    """Get all Plato events for a given date."""
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    events_result = service.events().list(
        calendarId='primary',
        timeMin=f'{date_str}T00:00:00+00:00',
        timeMax=f'{date_str}T23:59:00+00:00',
        singleEvents=True,
        orderBy='startTime',
        q='[Plato]'
    ).execute()
    
    return [
        {
            "title": e['summary'].replace('[Plato] ', ''),
            "start": e['start'].get('dateTime', ''),
            "end": e['end'].get('dateTime', ''),
            "id": e['id']
        }
        for e in events_result.get('items', [])
        if '[Plato]' in e.get('summary', '')
    ]


def create_event(service, date_str: str, start_time: str, end_time: str, 
                 title: str, description: str = None, color_id: str = None):
    """Create a single Google Calendar event."""
    
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
    return created


def create_weekly_events(service, schedule_events: list):
    """Create all events from Plato's planned schedule."""
    
    COLOR_MAP = {
        "cfa": "9",          # Blueberry
        "nitrogen": "10",    # Basil
        "glowbook": "6",     # Tangerine
        "plato": "7",        # Peacock
        "leetcode": "3",     # Grape
        "rest": "8",         # Graphite
        "exercise": "2",     # Sage
        "personal": "4",     # Flamingo
        "citco": "1",        # Lavender
        "audrey": "11",      # Tomato
    }
    
    created_count = 0
    for event in schedule_events:
        try:
            color = COLOR_MAP.get(event.get("category", ""), None)
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


# ============== SCHEDULE PROMPT ==============

def get_schedule_prompt(week_start: datetime) -> str:
    """Build the scheduling context for Claude."""
    template = get_weekly_template(week_start)
    
    return f"""
## WEEKLY SCHEDULE PLANNING

You are planning Jason's week starting {week_start.strftime('%A %B %d, %Y')}.

### Weekly Template
{json.dumps(template, indent=2)}

### Scheduling Rules
1. NEVER schedule over "work", "commute", "commute_prep", or "fixed" blocks
2. Only fill "free" blocks
3. CFA study gets priority — minimum 10 hours/week
4. Side projects (Nitrogen Tracker, Glowbook) — aim for 8-10 hours/week combined
5. LeetCode/interview prep — 3 sessions of 30-60 mins
6. Rest/downtime — at least 1 hour every evening, one long rest block on weekend
7. Exercise — Mon & Tue gym sessions are already fixed in template
8. Keep Sunday evening light — wind down for the work week
9. Batch similar work: don't alternate between CFA and coding in the same evening
10. Morning WFH blocks (07:30-09:00) are good for CFA study — fresh mind, no distractions
11. Audrey time may be declared spontaneously — leave some buffer, don't over-optimise

### Response Format
Return a plan_week action with an "events" array. Each event:
```
{{
    "date": "YYYY-MM-DD",
    "start": "HH:MM",
    "end": "HH:MM", 
    "title": "Short descriptive title",
    "description": "Optional detail or focus area",
    "category": "cfa|nitrogen|glowbook|plato|leetcode|rest|exercise|personal|citco|audrey"
}}
```

Include ALL allocated blocks for the week — study, projects, rest, exercise.
Be specific with titles: "CFA - Ethics Chapter 3" not just "CFA Study".
"""