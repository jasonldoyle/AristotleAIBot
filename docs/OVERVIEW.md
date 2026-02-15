# Plato - Personal AI Mentor Bot

## What Is Plato?

Plato is a personal AI mentor Telegram bot that uses Claude Sonnet to manage Jason's life across multiple domains: fitness tracking, project management, scheduling, finance, and accountability. Built with stoic wisdom principles, Plato tracks commitments, calls out deviations, and celebrates genuine progress.

## Tech Stack

- **Language**: Python 3.11+
- **AI**: Anthropic Claude Sonnet (via `anthropic` SDK)
- **Messaging**: Telegram Bot API (via `python-telegram-bot`)
- **Database**: Supabase (PostgreSQL)
- **Calendar**: Google Calendar API v3
- **Deployment**: Heroku worker dyno
- **Process**: `Procfile` → `plato_bot.py`

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
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase anon/service key |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `ALLOWED_USER_ID` | Jason's Telegram user ID (single-user bot) |
| `GOOGLE_REFRESH_TOKEN` | Google OAuth2 refresh token |
| `GOOGLE_CLIENT_ID` | Google OAuth2 client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth2 client secret |

## Domains

Plato manages 8 domains across 36 actions:

1. **Projects** - Work logging, goal tracking, pattern recognition
2. **Fitness** - Training blocks, workout tracking, progressive overload, nutrition, skincare, cycling
3. **Schedule** - Weekly planning, Google Calendar sync, check-ins
4. **Finance** - CSV imports (Revolut/AIB), budget tracking, spending reviews
5. **Admin** - One-off tasks, recurring tasks, important dates, reminders
6. **Ideas** - Idea parking lot with cooling period
7. **Soul Doc** - Life principles and goals
8. **Patterns** - Recurring behaviour tracking
