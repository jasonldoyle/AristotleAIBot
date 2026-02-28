# Actions Reference

All 21 actions Plato currently supports, grouped by domain.

## Soul Doc & Ideas (7 actions)

### `add_soul` — Store a goal, principle, or rule
```json
{"action": "add_soul", "category": "<category>", "content": "<text>"}
```
Categories: `goal_lifetime`, `goal_5yr`, `goal_2yr`, `goal_1yr`, `philosophy`, `rule`

### `update_soul` — Refine an existing soul doc entry
```json
{"action": "update_soul", "category": "<category>", "old_content": "<phrase from original>", "content": "<refined text>"}
```

### `query_soul` — Retrieve the full soul doc
```json
{"action": "query_soul"}
```

### `store_idea` — Capture an idea
```json
{"action": "store_idea", "idea": "<description>", "context": "<optional>"}
```

### `park_idea` — Park an idea for 14-day cooling
```json
{"action": "park_idea", "idea_id": "<uuid>"}
```

### `resolve_idea` — Approve or reject an idea
```json
{"action": "resolve_idea", "idea_id": "<uuid>", "status": "approved|rejected", "notes": "<optional>"}
```

### `query_ideas` — List all ideas
```json
{"action": "query_ideas"}
```

## Projects (6 actions)

### `create_project` — Create a new project
```json
{"action": "create_project", "name": "<name>", "slug": "<short-slug>", "intent": "<why this project exists>"}
```

### `log_work` — Log a work session
```json
{"action": "log_work", "slug": "<project-slug>", "summary": "<what was done>", "duration_mins": "<optional int>", "mood": "<optional>"}
```

### `add_goal` — Set a project goal
```json
{"action": "add_goal", "slug": "<project-slug>", "timeframe": "weekly|monthly|quarterly|milestone", "goal_text": "<the goal>", "target_date": "<optional ISO date>"}
```

### `achieve_goal` — Mark a goal as achieved
```json
{"action": "achieve_goal", "goal_id": "<uuid>"}
```

### `update_project` — Change project status
```json
{"action": "update_project", "slug": "<project-slug>", "status": "active|paused|completed|abandoned"}
```

### `query_projects` — List all active projects
```json
{"action": "query_projects"}
```

### `query_project` — Get detail on a specific project
```json
{"action": "query_project", "slug": "<project-slug>"}
```

## Schedule & Calendar (7 actions)

### `plan_week` — Generate a full weekly schedule
```json
{"action": "plan_week", "week": "this|next", "events": [{"date": "YYYY-MM-DD", "start": "HH:MM", "end": "HH:MM", "title": "<title>", "description": "<optional>", "category": "<project-slug>|rest|exercise|personal|citco|audrey"}]}
```
Creates a pending plan shown as a preview. Must be approved before pushing to Google Calendar.

### `approve_plan` — Approve a pending plan
```json
{"action": "approve_plan"}
```
Pushes the pending plan to Google Calendar and stores events in the database.

### `audrey_time` — Clear the evening for girlfriend time
```json
{"action": "audrey_time", "date": "YYYY-MM-DD"}
```
Cancels all Plato events from 18:00 onwards and creates an "Audrey Time" event.

### `report_deviation` — Log a schedule deviation
```json
{"action": "report_deviation", "date": "YYYY-MM-DD", "title": "<keyword from event>", "reason": "<what happened>"}
```

### `add_event` — Add a one-off calendar event
```json
{"action": "add_event", "date": "YYYY-MM-DD", "start": "HH:MM", "end": "HH:MM", "title": "<title>", "category": "personal", "description": "<optional>"}
```

### `cancel_event` — Cancel a specific event
```json
{"action": "cancel_event", "date": "YYYY-MM-DD", "title": "<keyword from event title>"}
```

### `edit_event` — Move or rename an event
```json
{"action": "edit_event", "date": "YYYY-MM-DD", "title": "<keyword>", "new_date": "<optional>", "new_start": "<optional>", "new_end": "<optional>", "new_title": "<optional>"}
```
Only include fields that are changing.

## Action Rules

- Only ONE action block per message
- JSON block must be at the very start of the reply, wrapped in ` ```json ... ``` ` fences
- The JSON block is the ONLY way to persist data — plain text descriptions do not save anything
- If no action is needed, respond normally without a JSON block
