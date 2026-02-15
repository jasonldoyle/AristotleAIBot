"""
Fitness domain — training, nutrition, skincare, cycling, body composition.
"""

from datetime import datetime
from plato.db import (
    get_current_block, get_all_lift_latest, get_recent_nutrition,
    get_weight_history, get_recent_training, MAIN_LIFTS,
    get_fitness_goals, get_phase_for_month,
)


def get_action_schemas() -> str:
    return """
### FITNESS ACTIONS:

**LOG WORKOUT** - He's reporting a gym session
```json
{"action": "log_workout", "session_type": "Push|Legs|Upper Hypertrophy|Shoulders + Arms", "exercises": [
    {"exercise": "Incline Barbell Press", "sets": 4, "reps": 8, "weight_kg": 60, "notes": null},
    {"exercise": "Cable Flye", "sets": 3, "reps": 15, "weight_kg": 15, "notes": null}
], "feedback": "felt strong today", "duration_mins": 65, "date": null}
```
Parse naturally: "Push day done, incline 4x8 at 60kg, cable flyes 3x15" → structured session.
Main lifts (Incline Bench, Barbell Row, Back Squat, OHP) are auto-tracked for progressive overload.
When a main lift hits the TOP of its rep range (8 for most, 10 for squats), prompt Jason to confirm the 2.5kg increase.

**DAILY LOG** - Morning check-in or anytime daily data
```json
{"action": "daily_log", "date": null, "weight_kg": 82.1, "steps": null, "sleep_hours": null,
  "skincare_am": true, "skincare_pm": true, "skincare_notes": null,
  "cycling_scheduled": false, "cycling_completed": true, "cycling_notes": null,
  "urticaria_severity": null, "breakout_severity": null, "breakout_location": null,
  "health_notes": null}
```
Only include fields Jason mentions. Exception-based: skincare defaults to done, cycling defaults to completed on scheduled days.

**MISSED WORKOUT** - He missed a scheduled session
```json
{"action": "missed_workout", "session_type": "Push|Legs|Upper Hypertrophy|Shoulders + Arms", "reason": "...", "date": null}
```

**CONFIRM LIFT PROGRESSION** - He confirms moving up weight
```json
{"action": "confirm_lift", "lift_key": "incline_bench|barbell_row|squat|ohp"}
```

**WEEKLY FITNESS SUMMARY** - Comprehensive weekly review (Sundays)
```json
{"action": "weekly_fitness_summary", "week_start": "YYYY-MM-DD"}
```

**BLOCK SUMMARY** - 4-week training block review
```json
{"action": "block_summary", "block_id": null}
```

**CREATE TRAINING BLOCK** - Start a new 4-week cycle
```json
{"action": "create_block", "name": "March 2026", "start_date": "2026-03-02", "end_date": "2026-03-29",
  "phase": "bulk", "calorie_target": 3000, "protein_target": 170,
  "weight_start": 82.0, "weight_target": 83.0,
  "cycling_days": ["Mon", "Wed", "Fri"], "notes": null}
```

**PLAN NEXT BLOCK** - Auto-plan next month's block
```json
{"action": "plan_next_block", "year": 2026, "month": 3, "weight_start": 82.5}
```

**TODAY'S WORKOUT** - Show today's scheduled session
```json
{"action": "todays_workout", "date": null}
```

**COMPLETE WORKOUT** - Mark session done (exception-based)
```json
{"action": "complete_workout", "date": null, "feedback": "felt good overall",
  "exceptions": [{"exercise": "Lateral Raise", "actual_reps": 6, "notes": "arms too tired by end"}]}
```

**ADJUST EXERCISE** - Change weight for any exercise
```json
{"action": "adjust_exercise", "exercise": "Lateral Raise", "new_weight": 8.0, "reason": "couldn't complete reps at 10kg"}
```

**PROGRESS PHOTOS** - Log that photos were taken
```json
{"action": "progress_photos", "date": null, "notes": "Front, side, back"}
```

**ADD FITNESS GOAL**
```json
{"action": "add_fitness_goal", "category": "body_composition|strength|aesthetic|habit|timeline",
  "goal_text": "Reach 88-89kg at 12-13% body fat", "target_value": "88-89kg @ 12-13% BF",
  "target_date": "2028-06-30", "notes": null}
```

**ACHIEVE FITNESS GOAL**
```json
{"action": "achieve_fitness_goal", "goal_fragment": "88-89kg"}
```

**REVISE FITNESS GOAL**
```json
{"action": "revise_fitness_goal", "goal_fragment": "88-89kg", "new_text": "Reach 90kg at 12% body fat", "new_target": "90kg @ 12% BF"}
```

### TRAINING PLAN CONTEXT:
Jason's 4-day split (Mon/Tue/Thu/Sat):
- Monday: Push (Chest/Shoulders/Triceps) — Main lift: Incline Barbell Press 4x6-8
- Tuesday: Legs + Abs — Main lift: Back Squat 4x8-10
- Thursday: Upper Hypertrophy — Main lifts: Incline Barbell Press 4x6-8, Barbell Row 4x6-8
- Saturday: Shoulders + Arms — Main lift: Overhead Barbell Press 4x6-8

Progressive overload rule: When he hits ALL sets at the TOP of the rep range → suggest +2.5kg.
Deload every 8 weeks: -10% weight, focus on form.
Aesthetic priorities: lateral delts (15+ sets/week), upper chest (15 sets/week), lat width (14 sets/week), abs (10+ sets/week).

WORKOUT COMPLETION FLOW:
- "What's my workout today?" → use todays_workout
- "Done, all good" → complete_workout with no exceptions
- "Done, except lat raises only 6 reps" → complete_workout with exception
- Silence on a training day = DO NOT auto-assume completed

### BODY COMPOSITION TARGETS:
Current: ~81kg @ ~22% BF
Timeline: Feb 2026 - Jun 2028 (28 months)
Goal: 88-89kg @ 12-13% BF

Phase timeline (auto-planned — use plan_next_block):
2026: Feb-May BULK, Jun MINI-CUT, Jul-Oct BULK, Nov MINI-CUT, Dec BULK
2027: Jan-May BULK, Jun MINI-CUT, Jul-Dec BULK
2028: Jan-Jun FINAL CUT

Nutrition auto-set by phase:
- Bulk: 3000 cal, 170g protein
- Mini-cut: 2450 cal, 180g protein
- Final cut: 2300 cal, 185g protein

### SKINCARE ROUTINE (exception-based tracking):
Morning: Water rinse → CeraVe Vitamin C Serum (10%) → CeraVe AM Facial Moisturising Lotion SPF50
Night: CeraVe Salicylic Acid Cleanser → CeraVe PM Facial Moisturising Lotion

### CYCLING (starts March 2026):
3 days/week, exception-based — assume completed unless Jason says otherwise.

### FITNESS GOALS:
Fitness goals are Jason's persistent body/training targets — reference them like you would the Soul Doc.
When he mentions a new fitness target, store it. When he hits one, celebrate and mark achieved."""


def get_context() -> str:
    """Build comprehensive fitness context."""
    try:
        context = "\n## FITNESS STATUS\n"
        has_data = False

        # Fitness goals
        goals = get_fitness_goals("active")
        if goals:
            has_data = True
            context += "\n### Fitness Goals:\n"
            by_cat = {}
            for g in goals:
                cat = g["category"]
                if cat not in by_cat:
                    by_cat[cat] = []
                by_cat[cat].append(g)
            for cat, items in by_cat.items():
                context += f"  {cat.upper()}:\n"
                for g in items:
                    context += f"    🎯 {g['goal_text']}"
                    if g.get("target_value"):
                        context += f" → {g['target_value']}"
                    if g.get("target_date"):
                        context += f" (by {g['target_date']})"
                    context += "\n"

        # Current training block
        block = get_current_block()
        if block:
            has_data = True
            context += f"\n### Current Block: {block['name']} ({block['phase'].upper()})\n"
            context += f"  {block['start_date']} → {block['end_date']}\n"
            if block.get("calorie_target"):
                context += f"  Targets: {block['calorie_target']} cal / {block.get('protein_target', '?')}g protein\n"
            if block.get("weight_start"):
                context += f"  Weight goal: {block['weight_start']}kg → {block.get('weight_target', '?')}kg\n"
        else:
            now = datetime.now()
            planned_phase = get_phase_for_month(now.year, now.month)
            context += f"\n### ⚠️ No active block! Expected phase: {planned_phase.upper()}\n"
            context += "  Suggest: 'Plan my [month] workouts' to create the block.\n"
            has_data = True

        # Recent weight
        weights = get_weight_history(days=14)
        if weights:
            has_data = True
            latest = weights[-1]
            context += f"\n### Weight: {latest['weight_kg']}kg ({latest['date']})\n"
            if len(weights) >= 2:
                change = round(float(weights[-1]["weight_kg"]) - float(weights[0]["weight_kg"]), 1)
                trend = f"+{change}" if change > 0 else str(change)
                context += f"  14-day trend: {trend}kg\n"

        # Main lift status
        lift_latest = get_all_lift_latest()
        if lift_latest:
            has_data = True
            context += "\n### Main Lifts (latest):\n"
            for key, data in lift_latest.items():
                config = MAIN_LIFTS[key]
                status = "🔥 HIT" if data["hit_target"] else "⏳"
                context += f"  {status} {config['name']}: {data['weight_kg']}kg × {data['sets']}×{data['reps']}"
                if data["hit_target"] and data.get("next_weight_kg"):
                    if not data.get("confirmed"):
                        context += f" → PENDING: move to {data['next_weight_kg']}kg?"
                    else:
                        context += f" → CONFIRMED: {data['next_weight_kg']}kg next"
                context += "\n"

        # Recent training (last 7 days)
        sessions = get_recent_training(days=7)
        if sessions:
            has_data = True
            completed = [s for s in sessions if s["completed"]]
            context += f"\n### This Week: {len(completed)}/4 sessions\n"
            for s in sessions:
                icon = "✅" if s["completed"] else "❌"
                context += f"  {icon} {s['date']}: {s['session_type']}"
                if s.get("feedback"):
                    context += f" — {s['feedback']}"
                context += "\n"

        # Recent nutrition (last 7 days)
        nutrition = get_recent_nutrition(days=7)
        if nutrition:
            has_data = True
            avg_cals = round(sum(n["calories"] for n in nutrition) / len(nutrition))
            avg_protein = round(sum(n["protein_g"] for n in nutrition) / len(nutrition))
            context += f"\n### Nutrition (7-day avg): {avg_cals} cal / {avg_protein}g protein"
            context += f" ({len(nutrition)} days logged)\n"

            low_cal = sum(1 for n in nutrition if n["calories"] < 2800)
            low_protein = sum(1 for n in nutrition if n["protein_g"] < 160)
            if low_cal:
                context += f"  ⚠️ {low_cal} days under 2800 cal\n"
            if low_protein:
                context += f"  ⚠️ {low_protein} days under 160g protein\n"

        if not has_data:
            return ""

        return context

    except Exception as e:
        return f"\n## FITNESS STATUS\n  ⚠️ Error loading fitness data: {e}\n"
