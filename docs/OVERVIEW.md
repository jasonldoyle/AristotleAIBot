# Plato - Personal AI Mentor Bot

## What Is Plato?

Plato is a personal AI mentor Telegram bot that uses Claude Sonnet to hold Jason accountable to his life goals. Built with stoic wisdom principles, Plato tracks commitments, challenges vague thinking, and celebrates genuine progress.

## Tech Stack

- **Language**: Python 3.11+
- **AI**: Anthropic Claude Sonnet (via `anthropic` SDK)
- **Messaging**: Telegram Bot API (via `python-telegram-bot[job-queue]`)
- **Database**: PostgreSQL hosted on Supabase, accessed via SQLAlchemy + Alembic
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

## Current Features (Phase 1)

### Soul Doc
Jason's life goals and principles, stored by tier and referenced in every response.

| Category | Description |
|----------|-------------|
| `goal_lifetime` | Ultimate life vision |
| `goal_5yr` | Medium-term targets |
| `goal_2yr` | Near-term milestones |
| `goal_1yr` | This year's focus |
| `philosophy` | Core beliefs/values |
| `rule` | Hard boundaries |

Actions: `add_soul`, `update_soul`, `query_soul`

### Ideas
Idea capture with optional 14-day cooling period for impulse control.

Actions: `store_idea`, `park_idea`, `resolve_idea`, `query_ideas`

## Architecture

```
Telegram message
    → handlers.py (auth, save to history)
    → prompts/ (build system prompt with soul doc + action schemas)
    → Claude API call
    → handlers.py (extract JSON action block if present)
    → actions.py (route to DB operation)
    → Reply to user with action status + Claude's response
```

## Database Tables

| Table | Migration | Description |
|-------|-----------|-------------|
| `conversations` | 001 | Chat history |
| `soul_doc` | 002 | Life goals and principles |
| `ideas` | 002 | Idea storage with optional parking |

## Project Structure

```
plato/
├── config.py          # Env vars, DB engine, Anthropic client
├── models.py          # SQLAlchemy models
├── handlers.py        # Telegram message handlers
├── actions.py         # Action router (JSON → DB operations)
├── db/
│   ├── core.py        # Conversation CRUD
│   ├── soul.py        # Soul doc CRUD
│   └── ideas.py       # Ideas CRUD
└── prompts/
    ├── base.py        # Base personality + soul doc injection
    └── __init__.py    # System prompt builder + action schemas
```
