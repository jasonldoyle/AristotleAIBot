# Architecture

## Entry Point Flow

```
Telegram Message
    |
    v
plato_bot.py          → Application setup, command/message handlers, scheduled jobs
    |
    v
plato/handlers.py     → Message routing, intent detection, Claude API calls
    |
    v
plato/prompts/        → System prompt assembly (intent-based domain selection)
    |
    v
Claude Sonnet API     → Returns text + optional JSON action block
    |
    v
plato/actions.py      → Processes JSON actions, calls db/ and plato_calendar.py
    |
    v
plato/db/             → Supabase CRUD operations (one file per domain)
plato_calendar.py     → Google Calendar API operations
```

## Module Dependency Diagram

```
plato_bot.py
  +-- plato/config.py        (env vars, clients: supabase, anthropic)
  +-- plato/handlers.py       (message handling, Claude API calls)
  |     +-- plato/prompts/    (system prompt construction)
  |     |     +-- plato/db/   (context data from Supabase)
  |     +-- plato/actions.py  (action processing)
  |           +-- plato/db/   (data mutations)
  |           +-- plato_calendar.py (Google Calendar)
  +-- plato/nudges.py         (scheduled proactive messages)
        +-- plato/db/         (schedule + task queries)
```

## Key Components

### handlers.py
- `handle_message()` - Main message handler: detects plan-week requests, MFP pastes, approval commands; builds prompt; calls Claude; parses JSON actions
- `handle_document()` - File upload handler for CSVs and MFP text files
- `start()`, `status()`, `clear_history()` - Telegram command handlers

### prompts/ (package)
- `build_system_prompt(message)` - Orchestrator: detects intent, assembles base + relevant domain schemas + context
- `build_messages_with_history()` - Builds message list with last 10 conversation turns
- Intent detection via keyword matching per domain
- Context builders pull live data from Supabase

### actions.py
- `process_action(action_data, raw_message)` - Router dispatching to per-action processors
- Each action processor validates data, calls db functions, returns status message
- Calendar actions call `plato_calendar.py` for Google Calendar sync

### db/ (package)
- `core.py` - Conversation history
- `projects.py` - Project CRUD, work logs, goals, patterns
- `fitness.py` - Training sessions, daily logs, nutrition, blocks, templates
- `schedule.py` - Calendar events, pending plans, adherence
- `finance.py` - CSV parsing, transactions, budgets
- `admin.py` - Tasks, recurring tasks, important dates
- `ideas.py` - Idea parking lot
- `soul_doc.py` - Soul doc entries

### plato_calendar.py
- Google Calendar OAuth2 (refresh token flow)
- Weekly template generation (office vs WFH days, fixed commitments)
- Event CRUD: create, clear, cancel evening events
- Schedule prompt builder for week planning

### nudges.py
- `check_for_nudges()` - Every 5 min: checks if a schedule block just ended
- `morning_briefing()` - 7:30am: today's tasks, dates, schedule
- `overdue_check()` - 2pm: overdue task reminders

## Design Decisions

- **Single-user bot**: All operations tied to `ALLOWED_USER_ID`
- **Action-based**: Claude returns JSON action blocks parsed from markdown code fences
- **Exception-based tracking**: Skincare and cycling default to "done" unless exceptions reported
- **Pending plan flow**: Week plans are staged → reviewed → approved before pushing to Google Calendar
- **Progressive overload**: Main lifts auto-tracked; hitting top of rep range triggers progression prompt
