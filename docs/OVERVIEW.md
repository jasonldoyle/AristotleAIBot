# Plato - Personal AI Mentor Bot

## What Is Plato?

Plato is a personal AI mentor Telegram bot that uses Claude Sonnet to hold Jason accountable to his life goals. Built with stoic wisdom principles, Plato tracks commitments, challenges vague thinking, and celebrates genuine progress.

## Tech Stack

- **Language**: Python 3.11+
- **AI**: Anthropic Claude Sonnet (via `anthropic` SDK)
- **Messaging**: Telegram Bot API (via `python-telegram-bot[job-queue]`)
- **Database**: PostgreSQL hosted on Supabase, accessed via SQLAlchemy + Alembic
- **Calendar**: Google Calendar API (OAuth2 with refresh tokens)
- **Deployment**: Railway (persistent worker dyno, long-polling)
- **Process**: `Procfile` → `python plato_bot.py`

## How to Run Locally

1. Clone the repo
2. Create a virtual environment: `python -m venv venv && source venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Set environment variables (see below)
5. Run: `python plato_bot.py`

## Environment Variables

| Variable | Description |
|----------|-------------|
| `TELEGRAM_TOKEN` | Telegram Bot API token |
| `DATABASE_URL` | PostgreSQL connection string (Supabase direct connection) |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `ALLOWED_USER_ID` | Jason's Telegram user ID (single-user bot) |

## Current Features (Phases 0-3)

### Soul Doc
Life goals and principles stored by tier, referenced in every Claude response.

Categories: `goal_lifetime`, `goal_5yr`, `goal_2yr`, `goal_1yr`, `philosophy`, `rule`

### Ideas
Idea capture with optional 14-day cooling period for impulse control.

### Projects
Track active projects with goals, work logs, and soul doc alignment.

### Weekly Schedule Planning
Generate complete weekly calendars respecting fixed commitments (work, gym, family). Plans are previewed in Telegram, then pushed to Google Calendar on approval.

### Calendar Management
Add, edit, cancel individual events. Audrey time clears evenings. Deviation tracking logs what changed.

See `docs/features/` for detailed documentation on each feature.

## Architecture

```
Telegram message
    → handlers.py (auth, save to history)
    → prompts/ (build system prompt with soul doc + projects + schedule + action schemas)
    → Claude API call
    → handlers.py (extract JSON action block if present)
    → actions.py (route to DB operation + Google Calendar)
    → Reply to user with action status + Claude's response
```

## Database Tables

| Table | Migration | Description |
|-------|-----------|-------------|
| `conversations` | 001 | Chat history |
| `soul_doc` | 002 | Life goals and principles |
| `ideas` | 002 | Idea storage with optional parking |
| `projects` | 003 | Project tracking |
| `project_goals` | 003 | Project milestones by timeframe |
| `project_logs` | 003 | Work session logs |
| `schedule_events` | 004 | Calendar events with status tracking |
| `pending_plans` | 004 | Staged weekly plans awaiting approval |

## Project Structure

```
plato/
├── config.py          # Env vars, DB engine, Anthropic client
├── models.py          # SQLAlchemy models (9 tables)
├── handlers.py        # Telegram message handlers
├── actions.py         # Action router (JSON → DB + Calendar operations)
├── calendar.py        # Google Calendar integration + schedule templates
├── db/
│   ├── core.py        # Conversation CRUD
│   ├── soul.py        # Soul doc CRUD
│   ├── ideas.py       # Ideas CRUD
│   ├── projects.py    # Projects, goals, work logs
│   └── schedule.py    # Schedule events, pending plans, deviations
└── prompts/
    ├── base.py        # Base personality + soul doc + projects + schedule injection
    └── __init__.py    # System prompt builder + action schemas
```
