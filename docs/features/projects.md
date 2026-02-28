# Projects

Plato tracks personal projects with goals, work logs, and status management. Projects are referenced throughout the system — in schedule planning, soul doc alignment, and accountability conversations.

## Concepts

- **Project** — A named initiative with a slug (short identifier), intent statement, and status
- **Goal** — A target attached to a project with a timeframe (weekly, monthly, quarterly, milestone)
- **Work Log** — A record of a work session with summary, optional duration, and mood

## Actions

### create_project

Create a new project.

```json
{
  "action": "create_project",
  "name": "Plato Bot",
  "slug": "plato",
  "intent": "Build an AI-powered personal mentor on Telegram"
}
```

- `slug` must be unique and is used as the identifier everywhere (schedule categories, queries, logs)
- `intent` captures the "why" — referenced by Claude for motivation and prioritisation

### log_work

Record a work session.

```json
{
  "action": "log_work",
  "slug": "plato",
  "summary": "Implemented dual-week schedule templates",
  "duration_mins": 90,
  "mood": "focused"
}
```

- `duration_mins` and `mood` are optional
- Logs build a history that Claude uses to track momentum and spot patterns

### add_goal

Set a project goal.

```json
{
  "action": "add_goal",
  "slug": "plato",
  "timeframe": "monthly",
  "goal_text": "Complete Phase 3 — scheduling and calendar integration",
  "target_date": "2026-02-28"
}
```

Timeframes: `weekly`, `monthly`, `quarterly`, `milestone`.

### achieve_goal

Mark a goal as achieved.

```json
{
  "action": "achieve_goal",
  "goal_id": "<uuid>"
}
```

### update_project

Change project status.

```json
{
  "action": "update_project",
  "slug": "plato",
  "status": "completed"
}
```

Statuses: `active`, `paused`, `completed`, `abandoned`.

### query_projects

List all active projects with their goals and recent logs.

### query_project

Get detailed view of a single project by slug.

## How Projects Feed Into Scheduling

When Claude plans a week, it receives:
- All active projects with their goals and deadlines
- The soul doc (life priorities)
- Available free blocks in the week template

Claude distributes project work across free blocks based on priority, deadlines, and goal alignment. Project slugs become the `category` field on calendar events, which maps to Google Calendar colors.

## Key Files

- `plato/actions.py` — Action handlers for all project operations
- `plato/db/projects.py` — Database CRUD for projects, goals, and work logs
- `plato/models.py` — `Project`, `ProjectGoal`, `ProjectLog` SQLAlchemy models
- `plato/prompts/base.py` — Injects active projects into Claude's system prompt
