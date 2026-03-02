# Actions Reference

All 30 actions Plato currently supports, grouped by domain.

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
Creates a pending plan shown as a preview. Auto-completes unlogged gym sessions from the current week (silence = compliance) and shows workout prescriptions with exact weight x reps. Must be approved before pushing to Google Calendar.

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

## Fitness (9 actions)

### `log_workout` — Log exercise numbers or session variations
```json
{"action": "log_workout", "day_label": "day1_chest|day2_back|day3_legs|day4_shoulders", "date": "YYYY-MM-DD", "status": "completed|partial|deload", "feedback": "<optional>", "lifts": [{"exercise": "incline_bb_press", "sets": 4, "reps": 8, "weight_kg": 80.0, "rpe": 8}]}
```
Only use when there's something worth recording — silence means compliance. Exercise slugs must match TRAINING_SPLIT exactly. Reported numbers sync the automatic progression tracker.

### `missed_workout` — Log a missed session
```json
{"action": "missed_workout", "day_label": "<day_label>", "date": "YYYY-MM-DD", "reason": "<optional>"}
```

### `log_weight` — Weekly weigh-in
```json
{"action": "log_weight", "weight_kg": 82.3, "date": "YYYY-MM-DD", "notes": "<optional>"}
```
Returns trend (4-week avg, rate/week) and current phase context.

### `log_nutrition` — Daily nutrition from MFP export
```json
{"action": "log_nutrition", "days": [{"date": "YYYY-MM-DD", "calories": 2850, "protein_g": 172, "carbs_g": 300, "fat_g": 70}, ...]}
```
Parse TOTALS row for each day from MyFitnessPal food diary export.

### `log_sleep` — Daily sleep hours
```json
{"action": "log_sleep", "hours": 7.5, "date": "YYYY-MM-DD", "notes": "<optional>"}
```
Flags if 7-day average drops below 7 hours.

### `modify_workout` — Adjust the workout template
```json
{"action": "modify_workout", "exercise": "<slug>", "modification_type": "reduce_volume|increase_volume|swap|adjust_weight|skip|custom", "detail": "<description>", "reason": "<optional>", "valid_from": "YYYY-MM-DD", "valid_until": "YYYY-MM-DD|null"}
```
`valid_until`: null for permanent changes.

### `override_block` — Deviate from the planned phase timeline
```json
{"action": "override_block", "name": "<block name>", "phase": "bulk|mini_cut|final_cut|maintenance", "start_date": "YYYY-MM-DD", "calorie_target": 2400, "protein_target": 180, "fat_min": 50, "fat_max": 70, "notes": "<optional>"}
```
Rarely needed — phases auto-apply by date.

### `seed_progression` — Initialize exercise starting weights
```json
{"action": "seed_progression", "exercises": [{"exercise": "incline_bb_press", "weight_kg": 60}, {"exercise": "incline_db_press", "weight_kg": 22}]}
```
One-time setup per exercise for the progression engine. Each starts at bottom of its rep range. Optionally include `"starting_reps"` to override.

### `query_fitness` — Get fitness status
```json
{"action": "query_fitness"}
```
Returns phase, today's workout with prescribed weight x reps, weight trend, sleep avg, active mods, recent sessions.

## Action Rules

- Only ONE action block per message
- JSON block must be at the very start of the reply, wrapped in ` ```json ... ``` ` fences
- The JSON block is the ONLY way to persist data — plain text descriptions do not save anything
- If no action is needed, respond normally without a JSON block
