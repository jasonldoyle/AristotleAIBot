# Fitness

Plato tracks a 2-year aesthetic physique program (March 2026 – Summer 2028) targeting 85-88kg at 12-14% body fat. The system uses exception-based logging — gym sessions default to "completed as planned." Only deviations, specific numbers, or misses are recorded.

## Training Split

4-day upper/lower split, Mon/Tue/Fri/Sat:

| Day | Label | Focus | Duration |
|-----|-------|-------|----------|
| Monday | day1_chest | Chest + Side Delts + Triceps | 60-70 min |
| Tuesday | day2_back | Back + Rear Delts + Biceps + Yoke | 60-70 min |
| Friday | day3_legs | Legs + Abs | 55-65 min |
| Saturday | day4_shoulders | Shoulders + Arms + Upper Chest Top-Up | 55-65 min |

Rest days: Wednesday, Thursday, Sunday.

## Periodisation

Phases auto-derive from the current date using `PHASE_TIMELINE` — no user action needed. 10 phases over 2 years:

| Phase | Dates | Calories | Protein |
|-------|-------|----------|---------|
| Bulk 1 | Mar–Jun 2026 | 3,000 | 170g |
| Mini-Cut 1 | Jul 1–21, 2026 | 2,400 | 180g |
| Bulk 2 | Aug–Nov 2026 | 3,000 | 170g |
| Mini-Cut 2 | Dec 1–21, 2026 | 2,400 | 180g |
| Bulk 3 | Jan–Apr 2027 | 3,050 | 175g |
| Mini-Cut 3 | May 1–21, 2027 | 2,400 | 185g |
| Bulk 4 | Jun–Sep 2027 | 3,050 | 175g |
| Mini-Cut 4 | Oct 1–21, 2027 | 2,400 | 185g |
| Bulk 5 | Nov–Dec 2027 | 3,000 | 175g |
| Final Cut | Jan–Jun 2028 | 2,300 | 185g |

Override with `override_block` to deviate from this timeline (e.g., start a cut early).

## Exception-Based Logging

The core design principle: **silence means compliance.** If Jason goes to the gym and does the planned workout, nothing is logged. Only these situations create records:

- Specific exercise numbers worth tracking (e.g., new PR, RPE note)
- Partial completion or variations from the template
- Missed sessions
- Workout template modifications

This keeps logging lightweight — no daily "did you go to gym?" prompts.

## Actions

### log_workout

Log specific exercise numbers or session variations. Only use when there's something worth recording.

```json
{
  "action": "log_workout",
  "day_label": "day1_chest",
  "date": "2026-03-02",
  "status": "completed",
  "feedback": "Felt strong today",
  "lifts": [
    {"exercise": "incline_bb_press", "sets": 4, "reps": 8, "weight_kg": 80.0, "rpe": 8}
  ]
}
```

- `lifts` array is optional — only include exercises worth recording
- `status`: completed, partial, deload
- `feedback` and `date` are optional (date defaults to today)

### missed_workout

Log a missed session. Claude suggests ramp-back modifications if appropriate.

```json
{
  "action": "missed_workout",
  "day_label": "day3_legs",
  "date": "2026-03-06",
  "reason": "Knee acting up"
}
```

### log_weight

Weekly weigh-in (Sunday mornings). Returns trend vs phase targets.

```json
{
  "action": "log_weight",
  "weight_kg": 82.3,
  "date": "2026-03-01",
  "notes": "Post-breakfast"
}
```

Response includes 4-week average, rate of change per week, and current phase context.

### log_nutrition

Monthly nutrition summary. Logged at end of month from MFP averages.

```json
{
  "action": "log_nutrition",
  "month": "2026-03",
  "avg_calories": 2850,
  "avg_protein_g": 172,
  "avg_carbs_g": 300,
  "avg_fat_g": 70,
  "notes": "Slightly under target on training days"
}
```

### log_sleep

Daily sleep tracking. Flags if 7-day average drops below 7 hours.

```json
{
  "action": "log_sleep",
  "hours": 7.5,
  "date": "2026-03-01",
  "notes": "Woke up once"
}
```

### modify_workout

Adjust the workout template. Modifications are stored in DB and applied on top of the baseline.

```json
{
  "action": "modify_workout",
  "exercise": "incline_bb_press",
  "modification_type": "reduce_volume",
  "detail": "3 sets instead of 4",
  "reason": "Arms fried from extra tricep work",
  "valid_from": "2026-03-03",
  "valid_until": "2026-03-15"
}
```

- `modification_type`: reduce_volume, increase_volume, swap, adjust_weight, skip, custom
- `valid_until`: null for permanent changes
- Active modifications appear in the system prompt next to the affected exercise

### override_block

Deviate from the hardcoded phase timeline. Rarely needed.

```json
{
  "action": "override_block",
  "name": "Early Mini-Cut",
  "phase": "mini_cut",
  "start_date": "2026-06-15",
  "calorie_target": 2400,
  "protein_target": 180,
  "fat_min": 50,
  "fat_max": 70,
  "notes": "Weight climbing too fast, starting cut 2 weeks early"
}
```

### query_fitness

Get full fitness status: current phase, today's workout with last-known weights, weight trend, sleep average, active modifications, recent sessions.

```json
{
  "action": "query_fitness"
}
```

## Prompt Injection

Every message to Claude includes a `## Fitness Status` section:

- **Phase** — current block name, date range, calorie/protein/fat targets
- **Today's workout** — exercises with last-known weights, sets, reps, and active modifications
- **Weight trend** — latest weigh-in, 4-week average, rate of change per week
- **Sleep** — 7-day average hours
- **Deload** — current week in the 8-week cycle
- **Active mods** — any workout modifications currently applied
- **Recent sessions** — last 4 training days with status

On rest days, shows "Rest day. Next session: [day/date]" instead of a workout.

## Progression Rules

Built into Claude's system prompt via `get_fitness_prompt()`:

- Hit top of rep range for all sets → increase weight next session
- Deload every 8 weeks (reduce weight 10%, maintain volume)
- Stall diagnosis priority: sleep → nutrition → recovery → program
- Bulk: surplus ≥ +300 kcal, focus on progressive overload
- Mini-cut: max 3 weeks, maintain intensity, accept small strength dips
- Final cut: patience over aggression, preserve muscle
- Fallback tiers: 3-day split → 2-day split → bodyweight if needed

## Key Files

- `plato/db/fitness.py` — All fitness CRUD, PHASE_TIMELINE, TRAINING_SPLIT, DAY_WEEKDAY_MAP, modification logic, formatting, static fitness rules
- `plato/actions.py` — 8 fitness action handlers
- `plato/models.py` — TrainingBlock, WorkoutSession, ExerciseLog, WorkoutModification, WeighIn, NutritionLog, SleepLog, DeloadTracker
- `plato/prompts/__init__.py` — 8 fitness action schemas
- `plato/prompts/base.py` — Fitness status + rules injection into system prompt
- `alembic/versions/005_add_fitness.py` — Migration for 8 fitness tables
