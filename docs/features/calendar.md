# Calendar Management

Beyond weekly planning, Plato supports managing individual calendar events — adding, editing, cancelling, and special modes like Audrey time.

## Actions

### add_event

Add a one-off event to Google Calendar.

```json
{
  "action": "add_event",
  "date": "2026-03-05",
  "start": "14:00",
  "end": "15:30",
  "title": "Dentist appointment",
  "category": "personal",
  "description": "Check-up at Dublin Dental"
}
```

### cancel_event

Remove an event by matching date and title keyword.

```json
{
  "action": "cancel_event",
  "date": "2026-03-05",
  "title": "Dentist"
}
```

Matches events containing the keyword in the title. Only removes `[Plato]`-prefixed events.

### edit_event

Move, reschedule, or rename an existing event.

```json
{
  "action": "edit_event",
  "date": "2026-03-05",
  "title": "Dentist",
  "new_date": "2026-03-06",
  "new_start": "10:00",
  "new_end": "11:00",
  "new_title": "Dentist check-up (rescheduled)"
}
```

All `new_*` fields are optional — only provided fields are updated.

### audrey_time

Clear the evening schedule for girlfriend time. Removes all `[Plato]` events after 18:00 on the given date and creates a single "Audrey Time" event.

```json
{
  "action": "audrey_time",
  "date": "2026-03-05"
}
```

### report_deviation

Log when the actual day deviated from the plan. Stored for pattern analysis.

```json
{
  "action": "report_deviation",
  "date": "2026-03-05",
  "title": "Gym session",
  "reason": "Felt exhausted after work, skipped gym"
}
```

## Google Calendar Colors

Each event category maps to a Google Calendar color:

| Category   | Color ID | Color Name |
|------------|----------|------------|
| citco      | 1        | Lavender   |
| exercise   | 2        | Sage       |
| leetcode   | 3        | Grape      |
| personal   | 4        | Flamingo   |
| glowbook   | 6        | Tangerine  |
| plato      | 7        | Peacock    |
| rest       | 8        | Graphite   |
| cfa        | 9        | Blueberry  |
| nitrogen   | 10       | Basil      |
| audrey     | 11       | Tomato     |

## Event Naming

All Plato-managed events are prefixed with `[Plato]` in Google Calendar. This allows:
- Easy visual identification of bot-managed vs manually-created events
- Safe bulk deletion when replanning a week (`clear_plato_events`)
- No interference with manually-created calendar events

## Key Files

- `plato/calendar.py` — All Google Calendar API operations (create, update, delete, query)
- `plato/actions.py` — Action handlers for add_event, cancel_event, edit_event, audrey_time, report_deviation
- `plato/db/schedule.py` — Schedule events and deviation tracking in database
