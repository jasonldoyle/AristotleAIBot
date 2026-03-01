# Weekly Schedule Planning

Plato generates complete weekly calendars that respect Jason's fixed commitments, work patterns, and personal preferences. Plans are previewed in Telegram for approval before being pushed to Google Calendar.

## How It Works

1. User says "plan this week" or "plan next week"
2. Claude receives a template of the week's time blocks (fixed + free)
3. Claude fills free blocks with project work, rest, and personal time based on active projects and soul doc goals
4. The full plan is presented in Telegram for review
5. User replies "approve" to push all events to Google Calendar

## Work Pattern

| Day       | Location | Gym   |
|-----------|----------|-------|
| Monday    | WFH      | 18:00 |
| Tuesday   | Office   | 19:45 |
| Wednesday | Office   | --    |
| Thursday  | Office   | --    |
| Friday    | WFH      | 18:00 |
| Saturday  | Home     | 11:15 |
| Sunday    | Home     | --    |

Office days: Tue/Wed/Thu (post-cutover March 1, 2026).
Gym days: Mon, Tue, Fri (evenings), Sat (after click & collect).

## Daily Block Templates

Each day is built from typed blocks. The scheduler never fills over non-free blocks.

### Block Types

| Type           | Meaning                              | Fillable? |
|----------------|--------------------------------------|-----------|
| `work`         | Citco work hours                     | No        |
| `commute_prep` | Getting ready for office             | No        |
| `commute`      | Travel (Luas, walking, gym transit)  | No        |
| `fixed`        | Locked commitments (gym, family, project work) | No |
| `free`         | Available for projects, rest, or personal time  | Yes |

### Monday (WFH + Gym)

```
07:30 - 09:00   fixed          Personal morning — do not schedule
09:00 - 18:00   work           Citco (WFH)
18:00 - 18:15   commute        Travel to gym
18:15 - 19:20   fixed          Gym session
19:20 - 19:40   commute        Travel home from gym
19:40 - 23:00   free           Evening block (3.3 hrs)
```

### Tuesday (Office + Gym)

```
07:30 - 08:00   commute_prep   Get ready, lift to Luas
08:00 - 09:00   commute        Luas to Citco
09:00 - 18:00   work           Citco (Office)
18:00 - 19:30   commute        Walk > Luas > Walk home
19:30 - 19:45   commute        Travel to gym
19:45 - 20:50   fixed          Gym session
20:50 - 21:10   commute        Travel home from gym
21:10 - 23:00   free           Evening block (1.8 hrs)
```

### Wednesday (Office, no gym)

```
07:30 - 08:00   commute_prep   Get ready, lift to Luas
08:00 - 09:00   commute        Luas to Citco
09:00 - 18:00   work           Citco (Office)
18:00 - 19:30   commute        Walk > Luas > Walk home
19:30 - 23:00   free           Evening block (3.5 hrs)
```

### Thursday (Office, no gym)

Same as Wednesday.

### Friday (WFH + Gym)

Same block structure as Monday.

### Saturday

```
07:30 - 09:00   fixed          Personal morning — do not schedule
09:15 - 10:45   fixed          Drive mam to guzheng school
10:45 - 11:15   fixed          Click & collect groceries
11:15 - 11:30   commute        Travel to gym
11:30 - 12:35   fixed          Gym session
12:35 - 12:50   commute        Travel home from gym
12:50 - 15:00   free           Afternoon block (2.2 hrs)
15:00 - 19:00   fixed          Project work
19:00 - 20:30   fixed          Pick up mam from guzheng
20:30 - 23:00   free           Evening block (2.5 hrs)
```

Saturday has a dedicated afternoon project work block (15:00-19:00) locked as fixed so Claude always assigns project work to it.

### Sunday

```
07:30 - 09:00   fixed          Personal morning — do not schedule
09:00 - 10:30   fixed          Drive mam to guzheng school
10:30 - 19:00   fixed          Project work
19:00 - 20:30   fixed          Pick up mam from guzheng
20:30 - 23:00   free           Evening block (keep light)
```

Sunday has a large dedicated project block (8.5 hrs). The evening is kept light for winding down before the work week.

## Scheduling Rules

Claude follows these rules when filling free blocks:

1. Never schedule over work, commute, commute_prep, or fixed blocks
2. Only fill free blocks with project work, rest, or personal time
3. Prioritise projects based on soul doc goals and deadlines
4. At least 1 hour rest every evening
5. Gym sessions are pre-set in the template — no duplicates
6. Weekend project blocks (Sat 15:00-19:00, Sun 10:30-19:00) are always project work
7. Sunday evening is kept light
8. Batch similar work — don't alternate projects in the same evening
9. All mornings (07:30-09:00) on WFH days and weekends are fixed personal time — never schedule anything there
10. Leave buffer for spontaneous Audrey time
11. Office days (Tue/Wed/Thu): only the evening post-commute block is free
12. WFH days (Mon/Fri): only the evening block is free (morning is personal time)
13. Keep project event titles simple — use the project name + general focus area, don't invent specific subtasks

## Google Calendar Integration

- Events are created with `[Plato]` prefix in the summary for identification
- Each category maps to a Google Calendar color (see calendar section below)
- `clear_plato_events()` removes all `[Plato]` events for a week before pushing a new plan
- Pending plans are stored in the `pending_plans` table until approved

## Key Files

- `plato/calendar.py` — Template generation (`get_weekly_template`), schedule prompt (`get_schedule_prompt`), Google Calendar API calls
- `plato/actions.py` — `plan_week` and `approve_plan` action handlers
- `plato/prompts/__init__.py` — `plan_week` action schema with `week` field
- `plato/prompts/base.py` — Week start calculation helpers
