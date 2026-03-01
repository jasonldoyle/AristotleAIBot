# Architecture

## Entry Point Flow

```
Telegram Message
    |
    v
plato_bot.py          → Application setup, command/message handlers
    |
    v
plato/handlers.py     → Auth check, conversation history, Claude API calls
    |
    v
plato/prompts/        → System prompt assembly (base + soul doc + projects + schedule + fitness + action schemas)
    |
    v
Claude Sonnet API     → Returns text + optional JSON action block
    |
    v
plato/actions.py      → Processes JSON actions, calls db/ and calendar.py
    |
    v
plato/db/             → PostgreSQL CRUD operations (one file per domain)
plato/calendar.py     → Google Calendar API operations
```

## Module Dependency Diagram

```
plato_bot.py
  +-- plato/config.py        (env vars, clients: SQLAlchemy engine, Anthropic)
  +-- plato/handlers.py       (message handling, Claude API calls)
  |     +-- plato/prompts/    (system prompt construction)
  |     |     +-- plato/db/   (context data from PostgreSQL)
  |     |     +-- plato/calendar.py (schedule template + prompt)
  |     +-- plato/actions.py  (action processing)
  |           +-- plato/db/   (data mutations)
  |           +-- plato/calendar.py (Google Calendar CRUD)
```

## Key Components

### handlers.py
- `handle_message()` — Main handler: auth check, save message, build prompt, call Claude, parse JSON action block, route to actions, reply
- `start()`, `status()`, `clear_history()` — Telegram command handlers
- Max tokens: 4096

### prompts/ (package)
- `build_system_prompt()` — Assembles base prompt + action schemas
- `build_messages_with_history()` — Last 10 conversation turns for Claude context
- `get_base_prompt()` — Personality, soul doc injection, active projects, today's schedule, fitness status
- Action schemas define all 29 actions with parameters, categories, and trigger conditions

### actions.py
- `process_action(action_data, raw_message)` — Match statement dispatching to per-action handlers
- Each handler validates data, calls db functions, returns status message
- Calendar actions call `calendar.py` for Google Calendar sync

### calendar.py
- Google Calendar OAuth2 (refresh token flow, app published to production)
- `get_weekly_template()` — Generates typed time blocks for each day (work, commute, fixed, free)
- `get_schedule_prompt()` — Builds scheduling rules and dual-week templates (this week + next week)
- Event CRUD: create, clear week, cancel event, edit event, audrey time

### db/ (package)
- `core.py` — Conversation history
- `soul.py` — Soul doc entries
- `ideas.py` — Idea parking lot
- `projects.py` — Projects, goals, work logs
- `schedule.py` — Schedule events, pending plans, deviations
- `fitness.py` — Training sessions, exercises, weight, nutrition, sleep, modifications, phase timeline

### models.py
SQLAlchemy models for all 17 tables: `Conversation`, `SoulDoc`, `Idea`, `Project`, `ProjectGoal`, `ProjectLog`, `ScheduleEvent`, `PendingPlan`, `TrainingBlock`, `WorkoutSession`, `ExerciseLog`, `WorkoutModification`, `WeighIn`, `NutritionLog`, `SleepLog`, `DeloadTracker`

## Design Decisions

- **Single-user bot**: All operations tied to `ALLOWED_USER_ID`
- **Action-based**: Claude returns JSON action blocks parsed from markdown code fences — this is the only way to persist data
- **Monolithic prompt**: All action schemas included in every call (no intent-based routing yet — planned for Phase 8 polish)
- **Pending plan flow**: Week plans are staged → previewed in Telegram → approved before pushing to Google Calendar
- **Exception-based tracking**: Default assumption is compliance; only deviations are logged (schedule and fitness)
- **Dual-week templates**: Schedule prompt includes both this week and next week templates so Claude always has correct dates
- **Auto-derived phases**: Fitness training phases are hardcoded in a timeline and auto-applied by date; override action only needed when deviating
