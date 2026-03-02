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

## Automatic Progression Engine

The progression engine prescribes **exact weight x reps** for every exercise, every session. No guesswork.

### How It Works

1. **Seed** — Jason provides starting weights for each exercise via `seed_progression`. Each exercise starts at the bottom of its rep range.
2. **Prescribe** — Every time Claude shows a workout (via `query_fitness` or `plan_week`), the system shows the exact prescribed weight x reps from the progression table.
3. **Advance** — Every 2 completed sessions at the same reps, the rep target increases by 1. When reps exceed the top of the exercise's range, weight increases by 2.5kg and reps reset to the bottom.
4. **Auto-complete** — When `plan_week` runs, any unlogged gym sessions from the current week are auto-completed at prescribed numbers. Silence = compliance. Progressions advance automatically.
5. **Override** — If Jason reports numbers different from prescribed (via `log_workout`), the system syncs progression to match his reality.

### Progression Rule

```
Start at bottom of rep range (e.g., 6 for "6-8")
  -> Every 2 sessions: +1 rep
  -> Hit top of range (e.g., 8 for "6-8"): +2.5kg, reset to bottom
```

Each exercise has its own rep range from TRAINING_SPLIT:
- `incline_bb_press` — "6-8" — progresses 6 -> 7 -> 8 -> +2.5kg
- `cable_fly_low_high` — "12-15" — progresses 12 -> 13 -> 14 -> 15 -> +2.5kg
- `calf_raise` — "15-20" — progresses 15 -> 16 -> ... -> 20 -> +2.5kg

### Exclusions

Exercises with "max" reps or time-based targets are excluded from auto-progression:
- `ab_wheel` (max reps)
- `farmers_carry` (time-based)

### Fallback Bootstrapping

If no progression entry exists but `exercise_logs` has historical data, the system auto-seeds from the last logged weight at the bottom of the rep range.

## Actions

### log_workout

Log specific exercise numbers or session variations. Only use when there's something worth recording. Reported numbers sync the progression tracker.

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
- `exercise` slugs must match TRAINING_SPLIT exactly (see `seed_progression` for the full list)
- `status`: completed, partial, deload
- `feedback` and `date` are optional (date defaults to today)
- When lifts are reported, the progression engine syncs to match the actual numbers and then advances

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

Daily nutrition from MyFitnessPal food diary export. Jason pastes MFP data (typically on Sundays) and Plato parses the TOTALS row for each day.

```json
{
  "action": "log_nutrition",
  "days": [
    {"date": "2026-03-01", "calories": 2850, "protein_g": 172, "carbs_g": 300, "fat_g": 70},
    {"date": "2026-03-02", "calories": 2920, "protein_g": 168, "carbs_g": 310, "fat_g": 75}
  ]
}
```

Returns per-day comparison to phase targets and weekly averages.

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

### seed_progression

Initialize exercise starting weights for the progression engine. One-time setup per exercise (or use to reset).

```json
{
  "action": "seed_progression",
  "exercises": [
    {"exercise": "incline_bb_press", "weight_kg": 60},
    {"exercise": "incline_db_press", "weight_kg": 22},
    {"exercise": "cable_fly_low_high", "weight_kg": 15}
  ]
}
```

Each exercise starts at the bottom of its own rep range. Optionally include `"starting_reps"` to override.

Valid exercise slugs:
- Day 1: incline_bb_press, incline_db_press, cable_fly_low_high, lateral_raise_db, lateral_raise_cable, tricep_pushdown, overhead_tricep_ext
- Day 2: pullup, chest_supported_row, straight_arm_pulldown, reverse_cable_fly, face_pull, barbell_curl, hammer_curl, db_shrug, neck_curl_ext, lateral_raise_finisher
- Day 3: back_squat, romanian_deadlift, leg_curl, calf_raise, cable_crunch, hanging_leg_raise (ab_wheel excluded)
- Day 4: db_shoulder_press, lateral_raise_heavy, lateral_raise_cable_drop, incline_db_fly, ss_curl_skull, ss_incline_curl_oh_ext, db_shrug, neck_curl_ext (farmers_carry excluded)

### query_fitness

Get full fitness status: current phase, today's workout with **prescribed** weight x reps from the progression engine, weight trend, sleep average, active modifications, recent sessions.

```json
{
  "action": "query_fitness"
}
```

## Prompt Injection

Every message to Claude includes a `## Fitness Status` section:

- **Phase** — current block name, date range, calorie/protein/fat targets
- **Today's workout** — exercises with prescribed weight x reps from the progression engine, and active modifications
- **Weight trend** — latest weigh-in, 4-week average, rate of change per week
- **Sleep** — 7-day average hours
- **Deload** — current week in the 8-week cycle
- **Active mods** — any workout modifications currently applied
- **Recent sessions** — last 4 training days with status

On rest days, shows "Rest day. Next session: [day/date]" instead of a workout.

## Progression Rules

Built into Claude's system prompt via `get_fitness_prompt()`:

- Progression is automatic — the system prescribes exact weight x reps for each exercise
- Every 2 completed sessions at same reps: +1 rep. Top of range: +2.5kg and reset.
- Silence = completed as prescribed. Progression advances automatically when plan_week runs.
- If Jason reports different numbers, progression syncs to match reality.
- Exercises with "max" reps or time-based (ab_wheel, farmers_carry) excluded from auto-progression.
- Deload every 8 weeks (reduce weight 10%, maintain volume)
- Stall diagnosis priority: sleep -> nutrition -> recovery -> program
- Bulk: surplus >= +300 kcal, focus on progressive overload
- Mini-cut: max 3 weeks, maintain intensity, accept small strength dips
- Final cut: patience over aggression, preserve muscle
- Fallback tiers: 3-day split -> 2-day split -> bodyweight if needed

## Key Files

- `plato/db/fitness.py` — All fitness CRUD, PHASE_TIMELINE, TRAINING_SPLIT, DAY_WEEKDAY_MAP, progression engine (seed, prescribe, advance, sync, auto-complete), modification logic, formatting, static fitness rules
- `plato/actions.py` — 9 fitness action handlers (8 original + seed_progression)
- `plato/models.py` — TrainingBlock, WorkoutSession, ExerciseLog, WorkoutModification, WeighIn, DailyNutrition, SleepLog, DeloadTracker, ExerciseProgression
- `plato/prompts/__init__.py` — 9 fitness action schemas
- `plato/prompts/base.py` — Fitness status + rules injection into system prompt
- `alembic/versions/005_add_fitness.py` — Migration for core fitness tables
- `alembic/versions/006_daily_nutrition.py` — Migration: monthly nutrition refactored to daily MFP entries
- `alembic/versions/007_exercise_progression.py` — Migration for exercise_progression table
