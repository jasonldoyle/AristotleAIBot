"""
Comprehensive fitness tracking database operations.
Handles daily logs, training sessions, main lift progression,
nutrition parsing (MFP), training blocks, and weekly/block summaries.
"""

import re
from datetime import datetime, timedelta
from plato.config import supabase, logger


# ============== MAIN LIFT CONFIG ==============

MAIN_LIFTS = {
    "incline_bench": {"name": "Incline Barbell Press", "rep_range": (6, 8), "increment": 2.5},
    "barbell_row": {"name": "Barbell Row", "rep_range": (6, 8), "increment": 2.5},
    "squat": {"name": "Back Squat", "rep_range": (8, 10), "increment": 2.5},
    "ohp": {"name": "Overhead Barbell Press", "rep_range": (6, 8), "increment": 2.5},
}

LIFT_ALIASES = {
    "incline bench": "incline_bench", "incline barbell": "incline_bench",
    "incline press": "incline_bench", "incline": "incline_bench",
    "barbell row": "barbell_row", "row": "barbell_row", "bent over row": "barbell_row",
    "squat": "squat", "back squat": "squat", "squats": "squat",
    "ohp": "ohp", "overhead press": "ohp", "shoulder press": "ohp",
    "military press": "ohp", "overhead barbell press": "ohp",
}

SESSION_TYPES = {
    "push": "Push", "chest": "Push",
    "legs": "Legs", "leg": "Legs",
    "upper": "Upper Hypertrophy", "upper hypertrophy": "Upper Hypertrophy",
    "shoulders": "Shoulders + Arms", "arms": "Shoulders + Arms",
    "shoulders + arms": "Shoulders + Arms", "shoulder": "Shoulders + Arms",
}


# ============== DAILY LOGS ==============

def log_daily(date: str = None, **kwargs) -> dict:
    """Log or update a daily entry. Upserts by date."""
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    entry = {"date": date}
    valid_fields = [
        "weight_kg", "steps", "cycling_scheduled", "cycling_completed",
        "cycling_notes", "skincare_am", "skincare_pm", "skincare_notes",
        "urticaria_severity", "breakout_severity", "breakout_location",
        "health_notes", "sleep_hours", "block_id"
    ]
    for field in valid_fields:
        if field in kwargs and kwargs[field] is not None:
            entry[field] = kwargs[field]

    result = supabase.table("daily_logs").upsert(
        entry, on_conflict="date"
    ).execute()
    return result.data[0] if result.data else entry


def get_daily_log(date: str) -> dict | None:
    """Get daily log for a specific date."""
    result = supabase.table("daily_logs").select("*").eq("date", date).execute()
    return result.data[0] if result.data else None


def get_daily_logs_range(start_date: str, end_date: str) -> list[dict]:
    """Get daily logs for a date range."""
    result = supabase.table("daily_logs").select("*").gte(
        "date", start_date
    ).lte("date", end_date).order("date").execute()
    return result.data


def get_weight_history(days: int = 30) -> list[dict]:
    """Get weight entries for the last N days."""
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    result = supabase.table("daily_logs").select(
        "date, weight_kg"
    ).gte("date", since).not_.is_("weight_kg", "null").order("date").execute()
    return result.data


# ============== TRAINING SESSIONS ==============

def log_training_session(
    session_type: str,
    exercises: list[dict],
    date: str = None,
    feedback: str = None,
    duration_mins: int = None
) -> dict:
    """Log a complete training session with exercises."""
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    normalized = SESSION_TYPES.get(session_type.lower(), session_type)
    block_id = _get_current_block_id(date)

    session = supabase.table("training_sessions").insert({
        "date": date,
        "session_type": normalized,
        "completed": True,
        "feedback": feedback,
        "duration_mins": duration_mins,
        "block_id": block_id,
    }).execute()

    session_id = session.data[0]["id"]
    main_lift_results = []

    for ex in exercises:
        exercise_name = ex["exercise"]
        is_main = _is_main_lift(exercise_name)

        supabase.table("training_exercises").insert({
            "session_id": session_id,
            "exercise_name": exercise_name,
            "sets": ex.get("sets"),
            "reps": ex.get("reps"),
            "weight_kg": ex.get("weight_kg"),
            "is_main_lift": is_main,
            "notes": ex.get("notes"),
        }).execute()

        if is_main and ex.get("weight_kg") and ex.get("sets") and ex.get("reps"):
            lift_key = _get_lift_key(exercise_name)
            if lift_key:
                prog = _track_main_lift(
                    date=date, lift_key=lift_key,
                    weight=ex["weight_kg"], sets=ex["sets"], reps=ex["reps"],
                )
                if prog:
                    main_lift_results.append(prog)

    return {
        "session": session.data[0],
        "exercise_count": len(exercises),
        "main_lift_progressions": main_lift_results,
    }


def log_missed_session(session_type: str, date: str = None, reason: str = None) -> dict:
    """Log a missed/skipped training session."""
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    normalized = SESSION_TYPES.get(session_type.lower(), session_type)
    block_id = _get_current_block_id(date)
    result = supabase.table("training_sessions").insert({
        "date": date, "session_type": normalized,
        "completed": False, "feedback": reason, "block_id": block_id,
    }).execute()
    return result.data[0]


def get_training_sessions_range(start_date: str, end_date: str) -> list[dict]:
    """Get training sessions for a date range with exercises."""
    sessions = supabase.table("training_sessions").select("*").gte(
        "date", start_date
    ).lte("date", end_date).order("date").execute()

    for session in sessions.data:
        exercises = supabase.table("training_exercises").select("*").eq(
            "session_id", session["id"]
        ).execute()
        session["exercises"] = exercises.data

    return sessions.data


def get_recent_training(days: int = 7) -> list[dict]:
    """Get training sessions from last N days."""
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    today = datetime.now().strftime("%Y-%m-%d")
    return get_training_sessions_range(since, today)


# ============== MAIN LIFT PROGRESSION ==============

def _is_main_lift(exercise_name: str) -> bool:
    return _get_lift_key(exercise_name) is not None


def _get_lift_key(exercise_name: str) -> str | None:
    name_lower = exercise_name.lower().strip()
    if name_lower in LIFT_ALIASES:
        return LIFT_ALIASES[name_lower]
    for alias, key in LIFT_ALIASES.items():
        if alias in name_lower or name_lower in alias:
            return key
    return None


def _track_main_lift(date: str, lift_key: str, weight: float, sets: int, reps: int) -> dict | None:
    config = MAIN_LIFTS[lift_key]
    target_top = config["rep_range"][1]
    hit_target = reps >= target_top and sets >= 4

    next_weight = weight + config["increment"] if hit_target else None

    entry = {
        "date": date, "lift_name": lift_key,
        "weight_kg": weight, "sets": sets, "reps": reps,
        "target_reps": target_top, "hit_target": hit_target,
        "next_weight_kg": next_weight, "confirmed": False,
    }

    try:
        supabase.table("main_lift_progress").insert(entry).execute()
    except Exception as e:
        logger.error(f"Failed to track main lift: {e}")
        return None

    return {
        "lift": config["name"], "lift_key": lift_key,
        "weight": weight, "sets": sets, "reps": reps,
        "hit_target": hit_target, "next_weight": next_weight,
    }


def get_lift_history(lift_key: str, limit: int = 12) -> list[dict]:
    result = supabase.table("main_lift_progress").select("*").eq(
        "lift_name", lift_key
    ).order("date", desc=True).limit(limit).execute()
    return result.data


def get_all_lift_latest() -> dict:
    latest = {}
    for key in MAIN_LIFTS:
        result = supabase.table("main_lift_progress").select("*").eq(
            "lift_name", key
        ).order("date", desc=True).limit(1).execute()
        if result.data:
            latest[key] = result.data[0]
    return latest


def confirm_progression(lift_key: str) -> str:
    result = supabase.table("main_lift_progress").select("*").eq(
        "lift_name", lift_key
    ).eq("hit_target", True).eq("confirmed", False).order(
        "date", desc=True
    ).limit(1).execute()

    if not result.data:
        return f"No pending progression for {lift_key}."

    entry = result.data[0]
    new_weight = entry["next_weight_kg"]

    # Confirm the progression
    supabase.table("main_lift_progress").update(
        {"confirmed": True}
    ).eq("id", entry["id"]).execute()

    # Update template weight for future session generation
    lift_name = MAIN_LIFTS[lift_key]["name"]
    update_template_weight(lift_name, float(new_weight))

    # Update weight on future scheduled (not yet completed) sessions
    try:
        future_sessions = supabase.table("training_sessions").select("id").eq(
            "completed", False
        ).gte("date", datetime.now().strftime("%Y-%m-%d")).execute()

        for session in future_sessions.data:
            supabase.table("training_exercises").update(
                {"weight_kg": new_weight}
            ).eq("session_id", session["id"]).ilike(
                "exercise_name", f"%{lift_name}%"
            ).execute()
    except Exception as e:
        logger.error(f"Failed to update future sessions: {e}")

    return f"✅ Confirmed: {lift_name} → {new_weight}kg (updated template + future sessions)"


# ============== NUTRITION LOGS ==============

def parse_mfp_diary(text: str) -> list[dict]:
    """Parse MyFitnessPal printable diary text into daily nutrition entries."""
    entries = []
    date_pattern = r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4})'
    sections = re.split(date_pattern, text)

    i = 1
    while i < len(sections) - 1:
        date_str = sections[i].strip()
        content = sections[i + 1]
        i += 2

        try:
            date_obj = datetime.strptime(date_str, "%b %d, %Y")
            date = date_obj.strftime("%Y-%m-%d")
        except ValueError:
            continue

        # Food TOTALS format: TOTALS{cal}{carbs}g{fat}g{protein}g...
        # Calories are 3-4 digits (500-9999), carbs follow with 'g' suffix
        # Exercise TOTALS have no 'g' markers so won't match
        totals_match = re.search(
            r'TOTALS(\d{3,4})(\d+)g(\d+)g(\d+)g',
            content
        )

        if totals_match:
            calories = int(totals_match.group(1))
            carbs = int(totals_match.group(2))
            fat = int(totals_match.group(3))
            protein = int(totals_match.group(4))

            meals = sum(1 for m in ["Breakfast", "Lunch", "Dinner", "Snacks"] if m in content)

            entries.append({
                "date": date,
                "calories": calories,
                "carbs_g": carbs,
                "fat_g": fat,
                "protein_g": protein,
                "meals_logged": meals,
            })

    return entries


def import_nutrition(entries: list[dict]) -> dict:
    imported = 0
    skipped = 0
    for entry in entries:
        try:
            supabase.table("nutrition_logs").upsert(entry, on_conflict="date").execute()
            imported += 1
        except Exception as e:
            logger.error(f"Failed to import nutrition for {entry.get('date')}: {e}")
            skipped += 1
    return {"imported": imported, "skipped": skipped}


def get_nutrition_range(start_date: str, end_date: str) -> list[dict]:
    result = supabase.table("nutrition_logs").select("*").gte(
        "date", start_date
    ).lte("date", end_date).order("date").execute()
    return result.data


def get_recent_nutrition(days: int = 7) -> list[dict]:
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    today = datetime.now().strftime("%Y-%m-%d")
    return get_nutrition_range(since, today)


# ============== TRAINING BLOCKS ==============

def create_training_block(
    name: str, start_date: str, end_date: str, phase: str,
    calorie_target: int = None, protein_target: int = None,
    weight_start: float = None, weight_target: float = None,
    cycling_days: list[str] = None, notes: str = None
) -> dict:
    result = supabase.table("training_blocks").insert({
        "name": name, "start_date": start_date, "end_date": end_date,
        "phase": phase, "calorie_target": calorie_target,
        "protein_target": protein_target, "weight_start": weight_start,
        "weight_target": weight_target, "cycling_days": cycling_days, "notes": notes,
    }).execute()
    return result.data[0]


def get_current_block(date: str = None) -> dict | None:
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    result = supabase.table("training_blocks").select("*").lte(
        "start_date", date
    ).gte("end_date", date).limit(1).execute()
    return result.data[0] if result.data else None


def _get_current_block_id(date: str) -> str | None:
    block = get_current_block(date)
    return block["id"] if block else None


# ============== SUMMARIES ==============

def generate_weekly_summary(week_start: str = None) -> dict:
    if not week_start:
        today = datetime.now()
        week_start = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")

    start = datetime.strptime(week_start, "%Y-%m-%d")
    end = start + timedelta(days=6)
    end_str = end.strftime("%Y-%m-%d")

    sessions = get_training_sessions_range(week_start, end_str)
    completed = [s for s in sessions if s["completed"]]
    missed = [s for s in sessions if not s["completed"]]

    daily = get_daily_logs_range(week_start, end_str)
    weights = [d["weight_kg"] for d in daily if d.get("weight_kg")]

    skincare_am = sum(1 for d in daily if d.get("skincare_am", True))
    skincare_pm = sum(1 for d in daily if d.get("skincare_pm", True))
    days_count = len(daily) or 7

    cycling_scheduled = sum(1 for d in daily if d.get("cycling_scheduled"))
    cycling_completed = sum(1 for d in daily if d.get("cycling_scheduled") and d.get("cycling_completed"))

    nutrition = get_nutrition_range(week_start, end_str)
    avg_cals = round(sum(n["calories"] for n in nutrition) / len(nutrition)) if nutrition else None
    avg_protein = round(sum(n["protein_g"] for n in nutrition) / len(nutrition)) if nutrition else None
    low_cal_days = sum(1 for n in nutrition if n["calories"] < 2800) if nutrition else None

    lift_latest = get_all_lift_latest()
    lift_progress = []
    for key, data in lift_latest.items():
        config = MAIN_LIFTS[key]
        entry = {
            "name": config["name"], "weight": data["weight_kg"],
            "sets": data["sets"], "reps": data["reps"],
            "hit_target": data["hit_target"],
        }
        if data["hit_target"] and data.get("next_weight_kg"):
            entry["progression"] = f"→ Moving to {data['next_weight_kg']}kg"
        lift_progress.append(entry)

    urticaria_days = [d for d in daily if d.get("urticaria_severity")]
    breakout_days = [d for d in daily if d.get("breakout_severity")]

    steps_entries = [d for d in daily if d.get("steps")]
    avg_steps = round(sum(d["steps"] for d in steps_entries) / len(steps_entries)) if steps_entries else None

    return {
        "week": f"{week_start} to {end_str}",
        "training": {
            "completed": len(completed), "total": len(sessions), "target": 4,
            "sessions": [{"type": s["session_type"], "date": s["date"]} for s in completed],
            "missed": [{"type": s["session_type"], "reason": s.get("feedback")} for s in missed],
        },
        "weight": {
            "start": weights[0] if weights else None,
            "end": weights[-1] if weights else None,
            "change": round(weights[-1] - weights[0], 1) if len(weights) >= 2 else None,
        },
        "nutrition": {
            "avg_calories": avg_cals, "avg_protein": avg_protein,
            "days_logged": len(nutrition), "low_cal_days": low_cal_days,
        },
        "main_lifts": lift_progress,
        "cycling": {"completed": cycling_completed, "scheduled": cycling_scheduled},
        "skincare": {"morning": skincare_am, "night": skincare_pm, "total_days": days_count},
        "health": {"urticaria_days": len(urticaria_days), "breakout_days": len(breakout_days)},
        "steps": {"avg": avg_steps},
    }


def generate_block_summary(block_id: str = None) -> dict:
    if block_id:
        result = supabase.table("training_blocks").select("*").eq("id", block_id).execute()
        block = result.data[0] if result.data else None
    else:
        block = get_current_block()

    if not block:
        return {"error": "No active training block found."}

    start = block["start_date"]
    end = block["end_date"]

    sessions = get_training_sessions_range(start, end)
    daily = get_daily_logs_range(start, end)
    nutrition = get_nutrition_range(start, end)

    completed = [s for s in sessions if s["completed"]]
    weights = [d["weight_kg"] for d in daily if d.get("weight_kg")]

    strength = {}
    for key in MAIN_LIFTS:
        history = supabase.table("main_lift_progress").select("*").eq(
            "lift_name", key
        ).gte("date", start).lte("date", end).order("date").execute()
        if history.data:
            first = history.data[0]
            last = history.data[-1]
            strength[key] = {
                "name": MAIN_LIFTS[key]["name"],
                "start_weight": first["weight_kg"],
                "end_weight": last["weight_kg"],
                "gain": round(last["weight_kg"] - first["weight_kg"], 1),
            }

    skincare_am = sum(1 for d in daily if d.get("skincare_am", True))
    skincare_pm = sum(1 for d in daily if d.get("skincare_pm", True))
    total_days = len(daily) or 28

    return {
        "block": block["name"], "phase": block["phase"],
        "dates": f"{start} to {end}",
        "training": {
            "total_sessions": len(completed), "target_sessions": 16,
            "adherence_pct": round(len(completed) / 16 * 100, 1),
        },
        "weight": {
            "start": weights[0] if weights else block.get("weight_start"),
            "end": weights[-1] if weights else None,
            "change": round(weights[-1] - weights[0], 1) if len(weights) >= 2 else None,
            "target": block.get("weight_target"),
        },
        "nutrition": {
            "avg_calories": round(sum(n["calories"] for n in nutrition) / len(nutrition)) if nutrition else None,
            "avg_protein": round(sum(n["protein_g"] for n in nutrition) / len(nutrition)) if nutrition else None,
            "days_logged": len(nutrition),
            "target_calories": block.get("calorie_target"),
            "target_protein": block.get("protein_target"),
        },
        "strength": strength,
        "skincare": {
            "morning_pct": round(skincare_am / total_days * 100, 1),
            "night_pct": round(skincare_pm / total_days * 100, 1),
        },
    }


# ============== PROGRESS PHOTOS ==============

def log_progress_photos(date: str = None, notes: str = None) -> dict:
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    block_id = _get_current_block_id(date)
    result = supabase.table("progress_photos").insert({
        "date": date, "block_id": block_id, "notes": notes,
    }).execute()
    return result.data[0]


# ============== FITNESS GOALS ==============

def add_fitness_goal(
    category: str, goal_text: str, target_value: str = None,
    target_date: str = None, notes: str = None
) -> dict:
    """Add a fitness goal. Categories: body_composition, strength, aesthetic, habit, timeline."""
    result = supabase.table("fitness_goals").insert({
        "category": category, "goal_text": goal_text,
        "target_value": target_value, "target_date": target_date,
        "notes": notes,
    }).execute()
    return result.data[0]


def get_fitness_goals(status: str = "active") -> list[dict]:
    """Get all fitness goals by status."""
    result = supabase.table("fitness_goals").select("*").eq(
        "status", status
    ).order("category").execute()
    return result.data


def achieve_fitness_goal(goal_fragment: str) -> bool:
    """Mark a fitness goal as achieved by partial text match."""
    goals = get_fitness_goals("active")
    for g in goals:
        if goal_fragment.lower() in g["goal_text"].lower():
            supabase.table("fitness_goals").update({
                "status": "achieved",
                "achieved_at": datetime.now().isoformat(),
            }).eq("id", g["id"]).execute()
            return True
    return False


def revise_fitness_goal(goal_fragment: str, new_text: str = None, new_target: str = None) -> bool:
    """Revise a fitness goal."""
    goals = get_fitness_goals("active")
    for g in goals:
        if goal_fragment.lower() in g["goal_text"].lower():
            updates = {"status": "revised"}
            if new_text:
                updates["goal_text"] = new_text
            if new_target:
                updates["target_value"] = new_target
            supabase.table("fitness_goals").update(updates).eq("id", g["id"]).execute()
            # Create new active version if revised
            if new_text:
                add_fitness_goal(
                    category=g["category"], goal_text=new_text,
                    target_value=new_target or g.get("target_value"),
                    target_date=g.get("target_date"),
                )
            return True
    return False


# ============== WORKOUT TEMPLATES ==============

def get_workout_template(session_type: str) -> list[dict]:
    """Get the exercise template for a session type."""
    result = supabase.table("workout_templates").select("*").eq(
        "session_type", session_type
    ).order("exercise_order").execute()
    return result.data


def get_all_templates() -> dict:
    """Get all workout templates grouped by session type."""
    result = supabase.table("workout_templates").select("*").order(
        "session_type"
    ).order("exercise_order").execute()

    templates = {}
    for row in result.data:
        st = row["session_type"]
        if st not in templates:
            templates[st] = []
        templates[st].append(row)
    return templates


def update_template_exercise(session_type: str, exercise_order: int, updates: dict) -> bool:
    """Update a specific exercise in a workout template."""
    result = supabase.table("workout_templates").update(updates).eq(
        "session_type", session_type
    ).eq("exercise_order", exercise_order).execute()
    return len(result.data) > 0


# ============== BLOCK WORKOUT GENERATION ==============

# Default weekly schedule: (day_of_week, session_type)
# 0=Mon, 1=Tue, 3=Thu, 5=Sat
WEEKLY_SCHEDULE = [
    (0, "Push"),
    (1, "Legs"),
    (3, "Upper Hypertrophy"),
    (5, "Shoulders + Arms"),
]

# Bulk/cut phase timeline — month: phase
# 2026: Feb-May bulk, June mini-cut, Jul-Oct bulk, Nov mini-cut
# 2027: Jan-May bulk, June mini-cut, Jul-Dec bulk
# 2028: Jan-Jun final cut
PHASE_TIMELINE = {
    (2026, 2): "bulk", (2026, 3): "bulk", (2026, 4): "bulk", (2026, 5): "bulk",
    (2026, 6): "mini_cut",
    (2026, 7): "bulk", (2026, 8): "bulk", (2026, 9): "bulk", (2026, 10): "bulk",
    (2026, 11): "mini_cut", (2026, 12): "bulk",
    (2027, 1): "bulk", (2027, 2): "bulk", (2027, 3): "bulk", (2027, 4): "bulk", (2027, 5): "bulk",
    (2027, 6): "mini_cut",
    (2027, 7): "bulk", (2027, 8): "bulk", (2027, 9): "bulk", (2027, 10): "bulk",
    (2027, 11): "bulk", (2027, 12): "bulk",
    (2028, 1): "final_cut", (2028, 2): "final_cut", (2028, 3): "final_cut",
    (2028, 4): "final_cut", (2028, 5): "final_cut", (2028, 6): "final_cut",
}

PHASE_NUTRITION = {
    "bulk": {"calories": 3000, "protein": 170},
    "mini_cut": {"calories": 2450, "protein": 180},
    "final_cut": {"calories": 2300, "protein": 185},
}


def calculate_block_dates(year: int, month: int) -> tuple[str, str]:
    """Calculate block start (first Monday) and end (last Sunday that includes month days).
    Block = first Monday of the month → the Sunday after the last day of the month."""
    import calendar

    # First Monday: find first day, advance to Monday
    first_day = datetime(year, month, 1)
    days_until_monday = (7 - first_day.weekday()) % 7
    if first_day.weekday() == 0:
        block_start = first_day  # Already Monday
    else:
        block_start = first_day + timedelta(days=days_until_monday)

    # Last day of month
    last_day_num = calendar.monthrange(year, month)[1]
    last_day = datetime(year, month, last_day_num)

    # End on Sunday: find the Sunday on or after the last day
    days_until_sunday = (6 - last_day.weekday()) % 7
    block_end = last_day + timedelta(days=days_until_sunday)

    return block_start.strftime("%Y-%m-%d"), block_end.strftime("%Y-%m-%d")


def get_phase_for_month(year: int, month: int) -> str:
    """Get the planned phase for a given month."""
    return PHASE_TIMELINE.get((year, month), "bulk")


def get_nutrition_for_phase(phase: str) -> dict:
    """Get calorie/protein targets for a phase."""
    return PHASE_NUTRITION.get(phase, PHASE_NUTRITION["bulk"])


def plan_next_block(year: int, month: int, weight_start: float = None) -> dict:
    """Auto-plan next block: calculates dates, phase, nutrition targets.
    Returns block config ready for create_training_block."""
    import calendar

    start_date, end_date = calculate_block_dates(year, month)
    phase = get_phase_for_month(year, month)
    nutrition = get_nutrition_for_phase(phase)
    month_name = calendar.month_name[month]

    return {
        "name": f"{month_name} {year}",
        "start_date": start_date,
        "end_date": end_date,
        "phase": phase,
        "calorie_target": nutrition["calories"],
        "protein_target": nutrition["protein"],
        "weight_start": weight_start,
    }


def generate_block_workouts(block_id: str, start_date: str, end_date: str) -> dict:
    """Generate all training sessions for a block with exercises from templates.
    Sessions only — no calendar events (scheduling is separate).
    Exercises include current working weights from templates."""

    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    templates = get_all_templates()
    sessions_created = []

    current = start
    while current <= end:
        weekday = current.weekday()

        for sched_day, session_type in WEEKLY_SCHEDULE:
            if weekday == sched_day and session_type in templates:
                date_str = current.strftime("%Y-%m-%d")

                session = supabase.table("training_sessions").insert({
                    "date": date_str,
                    "session_type": session_type,
                    "scheduled": True,
                    "completed": False,
                    "block_id": block_id,
                }).execute()

                session_id = session.data[0]["id"]

                for tmpl in templates[session_type]:
                    supabase.table("training_exercises").insert({
                        "session_id": session_id,
                        "exercise_name": tmpl["exercise_name"],
                        "sets": tmpl["sets"],
                        "reps": None,
                        "weight_kg": tmpl.get("current_weight_kg"),
                        "is_main_lift": tmpl["is_main_lift"],
                        "notes": f"Target: {tmpl['rep_range']} reps",
                    }).execute()

                sessions_created.append({
                    "date": date_str,
                    "session_type": session_type,
                    "session_id": session_id,
                    "exercises": len(templates[session_type]),
                })

        current += timedelta(days=1)

    return {
        "sessions_created": len(sessions_created),
        "sessions": sessions_created,
    }


# ============== LEGACY COMPATIBILITY ==============

def log_fitness_exercises(exercises: list[dict]) -> int:
    """Legacy compatibility wrapper."""
    if not exercises:
        return 0
    result = log_training_session(session_type="General", exercises=exercises)
    return result["exercise_count"]


def get_recent_fitness(days: int = 7) -> list[dict]:
    """Legacy compatibility wrapper."""
    sessions = get_recent_training(days)
    flat = []
    for s in sessions:
        for ex in s.get("exercises", []):
            flat.append({
                "session_date": s["date"],
                "exercise_name": ex["exercise_name"],
                "sets": ex.get("sets"),
                "reps": ex.get("reps"),
                "weight_kg": ex.get("weight_kg"),
                "notes": ex.get("notes"),
            })
    return flat


# ============== TODAY'S WORKOUT ==============

def get_todays_workout(date: str = None) -> dict | None:
    """Get today's scheduled (not yet completed) training session with exercises."""
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    sessions = supabase.table("training_sessions").select("*").eq(
        "date", date
    ).eq("completed", False).eq("scheduled", True).execute()

    if not sessions.data:
        return None

    session = sessions.data[0]
    exercises = supabase.table("training_exercises").select("*").eq(
        "session_id", session["id"]
    ).order("id").execute()

    session["exercises"] = exercises.data
    return session


def format_todays_workout(session: dict) -> str:
    """Format a scheduled session into a readable workout plan."""
    msg = f"🏋️ {session['session_type']} — {session['date']}\n\n"

    for i, ex in enumerate(session.get("exercises", []), 1):
        weight_str = f" @ {ex['weight_kg']}kg" if ex.get("weight_kg") else ""
        target = ex.get("notes", "").replace("Target: ", "") if ex.get("notes") else ""
        main = "⭐ " if ex.get("is_main_lift") else ""
        msg += f"{i}. {main}{ex['exercise_name']}: {ex['sets']} sets × {target}{weight_str}\n"

    return msg


# ============== WORKOUT COMPLETION ==============

def complete_workout(date: str = None, feedback: str = None, exceptions: list[dict] = None) -> dict:
    """Mark today's workout as completed with optional exceptions.
    
    exceptions format: [{"exercise": "Lateral Raise", "actual_reps": 6, "notes": "arms too tired"}]
    If no exceptions, all exercises assumed completed as planned.
    """
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    session = get_todays_workout(date)
    if not session:
        # Check if already completed
        done = supabase.table("training_sessions").select("*").eq(
            "date", date
        ).eq("completed", True).execute()
        if done.data:
            return {"error": "Already completed today's workout."}
        return {"error": "No scheduled workout found for today."}

    # Mark session completed
    supabase.table("training_sessions").update({
        "completed": True,
        "feedback": feedback,
    }).eq("id", session["id"]).execute()

    # Process exceptions — update specific exercises
    exception_results = []
    if exceptions:
        for exc in exceptions:
            exercise_name = exc.get("exercise", "").lower()
            for ex in session["exercises"]:
                if exercise_name in ex["exercise_name"].lower():
                    updates = {}
                    if "actual_reps" in exc:
                        updates["reps"] = exc["actual_reps"]
                    if "actual_weight" in exc:
                        updates["weight_kg"] = exc["actual_weight"]
                    if "notes" in exc:
                        updates["notes"] = exc["notes"]
                    if updates:
                        supabase.table("training_exercises").update(
                            updates
                        ).eq("id", ex["id"]).execute()
                        exception_results.append({
                            "exercise": ex["exercise_name"],
                            "changes": updates,
                        })
                    break

    # Track main lifts — use planned weights for completed-as-planned exercises
    main_lift_results = []
    for ex in session["exercises"]:
        if ex.get("is_main_lift") and ex.get("weight_kg"):
            lift_key = _get_lift_key(ex["exercise_name"])
            if lift_key:
                # Check if this exercise had an exception
                had_exception = any(
                    e["exercise"].lower() in ex["exercise_name"].lower()
                    for e in (exceptions or [])
                )
                if had_exception:
                    # Use exception reps if provided
                    exc_data = next(
                        (e for e in exceptions if e["exercise"].lower() in ex["exercise_name"].lower()),
                        {}
                    )
                    reps = exc_data.get("actual_reps", 0)
                else:
                    # Completed as planned — parse target reps from notes
                    target_str = (ex.get("notes") or "").replace("Target: ", "").split("-")
                    reps = int(target_str[-1].strip().split(" ")[0]) if target_str else 0

                if reps > 0:
                    prog = _track_main_lift(
                        date=date,
                        lift_key=lift_key,
                        weight=float(ex["weight_kg"]),
                        sets=ex["sets"],
                        reps=reps,
                    )
                    if prog:
                        main_lift_results.append(prog)

    return {
        "session_type": session["session_type"],
        "exercises": len(session["exercises"]),
        "exceptions": exception_results,
        "main_lift_progressions": main_lift_results,
    }


def update_template_weight(exercise_name: str, new_weight: float) -> bool:
    """Update the working weight for an exercise across all templates it appears in."""
    result = supabase.table("workout_templates").update({
        "current_weight_kg": new_weight
    }).ilike("exercise_name", f"%{exercise_name}%").execute()
    return len(result.data) > 0


def adjust_exercise_weight(exercise_name: str, new_weight: float) -> dict:
    """Adjust weight for any exercise — updates template + all future scheduled sessions."""
    # Update template
    template_updated = update_template_weight(exercise_name, new_weight)

    # Update all future uncompleted sessions
    future_sessions = supabase.table("training_sessions").select("id").eq(
        "completed", False
    ).gte("date", datetime.now().strftime("%Y-%m-%d")).execute()

    sessions_updated = 0
    for session in future_sessions.data:
        result = supabase.table("training_exercises").update(
            {"weight_kg": new_weight}
        ).eq("session_id", session["id"]).ilike(
            "exercise_name", f"%{exercise_name}%"
        ).execute()
        if result.data:
            sessions_updated += 1

    return {
        "exercise": exercise_name,
        "new_weight": new_weight,
        "template_updated": template_updated,
        "sessions_updated": sessions_updated,
    }