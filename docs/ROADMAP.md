# Plato v2 — Rebuild Roadmap

## Vision

Rebuild Plato from the ground up as a proper "second brain" assistant. Same Telegram + Claude architecture, but with:
- SQLAlchemy + Alembic (schema in repo, version-controlled migrations)
- Clean prompt system designed for cross-domain intelligence
- Domains rebuilt one at a time, tested before moving to next
- Same .env / API keys, Railway deployment (persistent worker)

## Design Principles

1. **Assume compliance** — Schedule, skincare, cycling default to "done". Jason only reports deviations.
2. **Cross-reference always** — New ideas checked against soul doc. Projects checked against goals. Reviews pull from all domains.
3. **Proactive + on-demand** — Bot nudges at scheduled times AND responds to manual triggers.
4. **Minimal prompts, maximum context** — Use a router/summarizer pattern instead of dumping raw schemas. More on this below.

## The Prompt Architecture Problem (and Solution)

**Problem:** One big prompt loses detail. Many small prompts lose cross-domain context.

**Solution: Router + Focused Context pattern**

```
Message arrives
    |
    v
ROUTER (lightweight Claude call or rule-based)
    → Classifies intent: log, query, plan, review, chat
    → Identifies domains: fitness, schedule, projects, etc.
    |
    v
CONTEXT BUILDER
    → Pulls ONLY relevant data from DB
    → Summarizes cross-domain connections (not raw dumps)
    → Injects soul doc excerpts relevant to the topic
    |
    v
DOMAIN PROMPT (focused)
    → Small, specific prompt for the classified intent
    → Has the action schemas it needs and nothing else
    → Has pre-summarized context, not raw table dumps
```

Key difference from v1: Context is **summarized before injection**, not dumped raw. The soul doc goals relevant to fitness don't need to include financial philosophy. The weekly review gets a pre-built summary of each domain, not every raw record.

---

## Phase 0: Foundation ✅
**Goal:** Bare minimum working bot with SQLAlchemy + Alembic, deployed on Railway.

### Tasks:
1. Delete all existing `plato/db/` files, `prompts_old.py`, `prompts/` domain files
2. Set up SQLAlchemy with PostgreSQL (keep Supabase as host, connect via connection string)
3. Set up Alembic (`alembic/` dir with migrations)
4. Create core models only:
   - `conversations` (chat history)
5. Rewrite `config.py` — SQLAlchemy engine + session instead of Supabase client
6. Update `requirements.txt` — replace `supabase` with `sqlalchemy`, `alembic`, `psycopg2-binary`
7. Minimal `handlers.py` — bot receives message, calls Claude with base prompt, replies
8. Base prompt only — Plato personality, no domain actions yet
9. Deploy to Railway (persistent worker dyno for long-polling)
10. Test: send a message, get a response, conversation saved to DB

**Deliverable:** Bot runs on Railway, responds to messages, stores conversation history. Nothing else yet.

---

## Phase 1: Soul Doc + Ideas ✅
**Goal:** The philosophical foundation. Soul doc is the north star everything else references.

### Models:
- `soul_doc` — category (goal_lifetime / goal_5yr / goal_2yr / goal_1yr / philosophy / rule), content, created_at, superseded_at
- `ideas` — idea, context, status (active/parked/approved/rejected), created_at, parked_at, eligible_date, resolution_notes

### Actions:
- `add_soul` — Add a life goal or principle
- `update_soul` — Refine/replace an existing soul doc entry
- `store_idea` — Store an idea
- `park_idea` — Park a stored idea with 14-day cooling period
- `resolve_idea` — Approve/reject an idea
- `query_soul` / `query_ideas` — Retrieve stored data

### Prompt:
- Soul doc always included in system prompt (grouped by tier: lifetime > 5yr > 2yr > 1yr > philosophy > rules)
- Action schemas with explicit trigger conditions
- Claude cross-references ideas against soul doc goals

### Verified:
- Soul doc entries stored and retrieved via Telegram
- Ideas stored via JSON action blocks
- Claude challenges vague goals before storing, refines via `update_soul`

---

## Phase 2: Projects
**Goal:** Track active projects with goals, work logs, and soul doc alignment.

### Models:
- `projects` — name, slug, intent, status, created_at
- `project_goals` — project_id, timeframe (weekly/monthly/quarterly/milestone), goal_text, target_date, achieved
- `project_logs` — project_id, summary, duration_mins, tags, mood, logged_at

### Actions:
- `create_project` — Claude checks soul doc alignment before confirming
- `log` — Log work on a project
- `add_goal` / `achieve_goal` — Project milestones
- Query project status

### Prompt:
- Active projects with current goals included when project domain detected
- Cross-reference: new project → soul doc check. Goal achieved → celebrate in context of bigger picture.

### Test scenarios:
- "I want to start working on a recipe app" → Claude checks soul doc, creates project if aligned
- "Worked on Plato for 2 hours, refactored the DB layer" → logged
- "How's my progress on CFA?" → summary with goals

---

## Phase 3: Schedule
**Goal:** Weekly planning with Google Calendar, deviation tracking, Audrey time. The week serves the year, which serves the 2yr, 5yr, and lifetime goals in the soul doc. Schedule planning should consult soul doc priorities to allocate subjective time.

### Models:
- `schedule_events` — date, start_time, end_time, title, category, status, deviation_reason
- `schedule_template` — Hardcoded weekly template (work, gym, mam, groceries)
- `pending_plan` — Staged weekly plan before approval

### Hard-coded template (fixed, non-negotiable blocks):
- Work: 9-6 (WFH or office depending on day, with commute on office days)
- Gym: Mon, Tue, Fri, Sat (times from fitness domain)
- Mam driving: Sat 9:15-10:45, Sun 9-10:30
- Groceries: Sat 10:45-11:15
- Subjective (planned around fixed blocks): project time, CFA study — allocated based on soul doc goal priorities
- Audrey time: wildcard override, can trump anything

### Actions:
- `plan_week` — Generate schedule around fixed blocks, push to Google Calendar
- `audrey_time` — Cancel evening plans
- `report_deviation` — Log what changed and why (for pattern tracking)
- `add_event` — One-off calendar event

### Deviation tracking:
- Schedule assumed followed by default
- End-of-day nudge: "Anything deviate from the plan today?"
- Deviations stored with reasons for weekly review pattern analysis

### Test scenarios:
- "Plan my week" → schedule generated respecting fixed blocks
- "Approve" → pushed to Google Calendar
- "Didn't do CFA tonight, went to cinema with Audrey" → deviation logged, no judgment
- End-of-day nudge fires, Jason reports or confirms compliance

---

## Phase 4: Fitness
**Goal:** Training tracking, progressive overload, daily logs, nutrition.

### Models:
- `training_blocks` — name, start/end dates, phase (bulk/mini_cut/final_cut), calorie/protein targets
- `training_sessions` — date, session_type, completed, feedback, block_id
- `training_exercises` — session_id, exercise_name, sets, reps, weight_kg, is_main_lift
- `workout_templates` — session_type, exercise_name, default sets/reps/weight, order
- `daily_logs` — date, weight_kg, sleep_hours, skincare_am/pm, cycling, health notes
- `nutrition_logs` — date, calories, protein, carbs, fat (from MFP imports)
- `fitness_goals` — category, goal_text, target_value, target_date, status

### Actions:
- `log_workout` / `complete_workout` — Full session or exception-based completion
- `daily_log` — Morning check-in (weight, sleep, skincare exceptions)
- `missed_workout` — Log why
- `confirm_lift` — Approve weight progression on main lifts
- `todays_workout` — Show what's scheduled
- `create_block` / `plan_next_block` — Training block management
- MFP diary import (text paste or file upload)

### Bulk/cut cycle:
- Annual phases defined in training blocks
- Nutrition targets adjust per phase
- Claude knows the cycle and advises accordingly

### Test scenarios:
- "Gym was good, hit all targets" → complete_workout with no exceptions
- "Couldn't finish squats, knee felt off" → logged with deviation
- "82.3kg this morning" → daily log, trend tracked
- [MFP paste] → nutrition imported, compared to block targets

---

## Phase 5: Finance + Admin
**Goal:** Bank imports, budget tracking, task management, important dates.

### Models:
- `transactions` — date, description, amount, category, source, is_transfer
- `budget_limits` — category, monthly_limit
- `admin_tasks` — title, due_date, category, priority, status, recurring fields
- `important_dates` — title, month, day, year, category, reminder_days

### Actions:
- CSV upload (Revolut/AIB) → auto-categorize and import
- `finance_review` — Monthly summary
- `set_budget` — Category spending limits
- `add_task` / `complete_task` / `skip_task` / `delete_task`
- `add_recurring` / `complete_recurring` / `delete_recurring`
- `add_date` / `delete_date`
- `show_tasks` — Today / upcoming / all

### Test scenarios:
- Upload Revolut CSV → transactions imported, budget alerts shown
- "Monthly finance review" → spending by category, savings rate
- "Remind me to renew insurance by March 15" → task created
- "Mam's birthday is March 15" → important date stored with reminder

---

## Phase 6: Reviews + Nudges
**Goal:** The intelligence layer. Weekly/monthly reviews that cross-reference everything.

### Weekly Review (Sunday evening, also triggerable):
- Schedule adherence: compliance %, deviation patterns
- Fitness: sessions completed, weight trend, main lift progress
- Projects: hours logged per project, goal progress
- Tasks: completed vs overdue
- Soul doc check: are actions aligned with stated goals?
- Pattern flags: recurring deviations, missed commitments

### Monthly Review (1st of month, also triggerable):
- Finance: income, spending, savings rate, budget adherence
- Nutrition: average calories/protein vs targets, compliance
- Fitness: block progress, body composition trend
- Projects: monthly velocity, goal completions
- Next month planning: new training block, schedule adjustments

### Nudges:
- Morning briefing (7:30am): today's schedule, tasks, reminders
- End-of-day deviation check (9:30pm): "Anything deviate from plan?"
- Overdue task reminder (2pm)
- Post-event check-in (5 min after scheduled block ends)
- Sunday weekly review prompt
- 1st of month review prompt

### Cross-domain intelligence:
- "You've missed CFA 3 weeks in a row — is this still a priority?"
- "Your spending on takeaway is up 40% — you're in a cut phase, watch it"
- "You parked 'recipe app' 14 days ago — still interested? It aligns with your 2yr goal of launching a SaaS"

---

## Phase 7: Polish + Hardening
**Goal:** Clean up, optimize, document.

### Tasks:
- Action registry pattern (replace if/elif chain in actions.py)
- Error handling audit
- Prompt token optimization (measure and trim)
- Update all docs (OVERVIEW, ARCHITECTURE, ACTIONS, PROMPTS)
- Delete dead code, unused imports
- Add /status command rebuild
- Edge case handling (empty DB, first-time setup, missing blocks)
- Deployment verification on Railway

---

## Migration Strategy

Since we're wiping data and starting fresh:
1. Keep Supabase as PostgreSQL host (no infra change needed)
2. Drop all existing tables
3. Alembic `upgrade head` creates fresh schema
4. Bot starts with empty DB — Phase 0 just needs conversations table
5. Each phase adds its migrations incrementally
6. Same .env file, same API keys throughout

## Deployment

Railway — persistent worker process running `python plato_bot.py` with long-polling. Supabase remains as the PostgreSQL host (connected via direct connection string instead of Supabase SDK). Same .env variables, just replacing `SUPABASE_URL`/`SUPABASE_KEY` with `DATABASE_URL` (PostgreSQL connection string).
