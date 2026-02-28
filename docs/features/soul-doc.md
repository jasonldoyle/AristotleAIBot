# Soul Doc & Ideas

The soul doc is Plato's foundation — a living document of Jason's goals, principles, and rules. It's injected into every Claude conversation so responses always align with what matters most.

## Soul Doc

### Categories

| Category        | Purpose                                    |
|-----------------|--------------------------------------------|
| `goal_lifetime` | Ultimate life vision                       |
| `goal_5yr`      | Medium-term targets (5 years)              |
| `goal_2yr`      | Near-term milestones (2 years)             |
| `goal_1yr`      | This year's focus                          |
| `philosophy`    | Core beliefs and values                    |
| `rule`          | Hard boundaries and non-negotiables        |

### Actions

**add_soul** — Store a new goal or principle.

```json
{
  "action": "add_soul",
  "category": "goal_1yr",
  "content": "Launch Plato Bot as a working personal mentor system"
}
```

**update_soul** — Refine an existing entry by matching a phrase.

```json
{
  "action": "update_soul",
  "category": "philosophy",
  "old_content": "phrase to match",
  "content": "refined version of the principle"
}
```

**query_soul** — Retrieve the full soul doc (all categories).

### How It's Used

The soul doc is loaded into Claude's system prompt on every message via `get_base_prompt()`. Claude references it when:
- Planning weekly schedules (prioritising projects that align with goals)
- Giving advice or accountability nudges
- Evaluating ideas against life direction
- Choosing how to frame responses (stoic, direct, encouraging)

## Ideas

A parking lot for ideas with a 14-day cooling period to prevent impulsive action.

### Lifecycle

```
store_idea → active (captured)
    ↓
park_idea → parked (14-day cooling)
    ↓
resolve_idea → approved / rejected
```

### Actions

**store_idea** — Capture an idea.

```json
{
  "action": "store_idea",
  "idea": "Build a habit tracker into Plato",
  "context": "Noticed I keep forgetting gym on office days"
}
```

**park_idea** — Start the 14-day cooling period.

```json
{
  "action": "park_idea",
  "idea_id": "<uuid>"
}
```

**resolve_idea** — Approve or reject after reflection.

```json
{
  "action": "resolve_idea",
  "idea_id": "<uuid>",
  "status": "approved",
  "notes": "Still relevant after 2 weeks — promote to project"
}
```

**query_ideas** — List all ideas with their statuses and age.

### Design Philosophy

The cooling period prevents "shiny object syndrome." Ideas are captured immediately so they aren't lost, but action is delayed so only genuinely valuable ideas survive.

## Key Files

- `plato/actions.py` — Soul doc and idea action handlers
- `plato/db/soul.py` — Soul doc database operations
- `plato/db/ideas.py` — Ideas database operations
- `plato/models.py` — `SoulDoc`, `Idea` SQLAlchemy models
- `plato/prompts/base.py` — Soul doc injection into system prompt
