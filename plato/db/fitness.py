"""Fitness domain: training blocks, workout sessions, exercise logs,
modifications, weigh-ins, nutrition, sleep, deload tracking."""

from datetime import datetime, timezone

from plato.config import SessionLocal
from plato.models import (
    TrainingBlock, WorkoutSession, ExerciseLog, WorkoutModification,
    WeighIn, NutritionLog, SleepLog, DeloadTracker,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PHASE_TIMELINE = [
    {"name": "Bulk 1",     "phase": "bulk",      "start": "2026-03-01", "end": "2026-06-30", "cals": 3000, "protein": 170, "fat_min": 60, "fat_max": 80},
    {"name": "Mini-Cut 1", "phase": "mini_cut",   "start": "2026-07-01", "end": "2026-07-21", "cals": 2400, "protein": 180, "fat_min": 50, "fat_max": 70},
    {"name": "Bulk 2",     "phase": "bulk",      "start": "2026-08-01", "end": "2026-11-30", "cals": 3000, "protein": 170, "fat_min": 60, "fat_max": 80},
    {"name": "Mini-Cut 2", "phase": "mini_cut",   "start": "2026-12-01", "end": "2026-12-21", "cals": 2400, "protein": 180, "fat_min": 50, "fat_max": 70},
    {"name": "Bulk 3",     "phase": "bulk",      "start": "2027-01-01", "end": "2027-04-30", "cals": 3050, "protein": 175, "fat_min": 60, "fat_max": 80},
    {"name": "Mini-Cut 3", "phase": "mini_cut",   "start": "2027-05-01", "end": "2027-05-21", "cals": 2400, "protein": 185, "fat_min": 50, "fat_max": 70},
    {"name": "Bulk 4",     "phase": "bulk",      "start": "2027-06-01", "end": "2027-09-30", "cals": 3050, "protein": 175, "fat_min": 60, "fat_max": 80},
    {"name": "Mini-Cut 4", "phase": "mini_cut",   "start": "2027-10-01", "end": "2027-10-21", "cals": 2400, "protein": 185, "fat_min": 50, "fat_max": 70},
    {"name": "Bulk 5",     "phase": "bulk",      "start": "2027-11-01", "end": "2027-12-31", "cals": 3000, "protein": 175, "fat_min": 60, "fat_max": 80},
    {"name": "Final Cut",  "phase": "final_cut", "start": "2028-01-01", "end": "2028-06-30", "cals": 2300, "protein": 185, "fat_min": 50, "fat_max": 70},
]

TRAINING_SPLIT = {
    "day1_chest": {
        "label": "Day 1: Chest + Side Delts",
        "weekday": "Monday",
        "duration": "60-70 min",
        "exercises": [
            {"name": "incline_bb_press", "display": "Incline Barbell Press (30°)", "sets": 4, "reps": "6-8"},
            {"name": "incline_db_press", "display": "Incline Dumbbell Press", "sets": 3, "reps": "10-12"},
            {"name": "cable_fly_low_high", "display": "Cable Fly (low-to-high)", "sets": 3, "reps": "12-15"},
            {"name": "lateral_raise_db", "display": "Dumbbell Lateral Raise", "sets": 4, "reps": "12-15"},
            {"name": "lateral_raise_cable", "display": "Cable Lateral Raise", "sets": 3, "reps": "15-20"},
            {"name": "tricep_pushdown", "display": "Tricep Pushdown", "sets": 3, "reps": "10-12"},
            {"name": "overhead_tricep_ext", "display": "Overhead Tricep Extension", "sets": 2, "reps": "12-15"},
        ],
    },
    "day2_back": {
        "label": "Day 2: Back + Rear Delts + Biceps + Yoke",
        "weekday": "Tuesday",
        "duration": "60-70 min",
        "exercises": [
            {"name": "pullup", "display": "Weighted Pull-up / Lat Pulldown", "sets": 4, "reps": "6-8"},
            {"name": "chest_supported_row", "display": "Chest-Supported Row", "sets": 3, "reps": "10-12"},
            {"name": "straight_arm_pulldown", "display": "Straight-Arm Lat Pulldown", "sets": 3, "reps": "12-15"},
            {"name": "reverse_cable_fly", "display": "Reverse Cable Fly", "sets": 3, "reps": "15-20"},
            {"name": "face_pull", "display": "Face Pulls", "sets": 3, "reps": "15-20"},
            {"name": "barbell_curl", "display": "Barbell Curl", "sets": 3, "reps": "8-10"},
            {"name": "hammer_curl", "display": "Hammer Curl", "sets": 3, "reps": "10-12"},
            {"name": "db_shrug", "display": "Dumbbell Shrugs", "sets": 3, "reps": "10-12"},
            {"name": "neck_curl_ext", "display": "Neck Curl / Extension", "sets": 2, "reps": "15-20"},
            {"name": "lateral_raise_finisher", "display": "Lateral Raise (finisher)", "sets": 2, "reps": "15-20"},
        ],
    },
    "day3_legs": {
        "label": "Day 3: Legs + Abs",
        "weekday": "Friday",
        "duration": "55-65 min",
        "exercises": [
            {"name": "back_squat", "display": "Back Squat", "sets": 4, "reps": "8-10"},
            {"name": "romanian_deadlift", "display": "Romanian Deadlift", "sets": 3, "reps": "10-12"},
            {"name": "leg_curl", "display": "Leg Curl", "sets": 3, "reps": "12-15"},
            {"name": "calf_raise", "display": "Calf Raises", "sets": 4, "reps": "15-20"},
            {"name": "cable_crunch", "display": "Cable Crunch", "sets": 3, "reps": "12-15"},
            {"name": "hanging_leg_raise", "display": "Hanging Leg Raise", "sets": 3, "reps": "12-15"},
            {"name": "ab_wheel", "display": "Ab Wheel / Plank", "sets": 2, "reps": "max"},
        ],
    },
    "day4_shoulders": {
        "label": "Day 4: Shoulders + Arms + Upper Chest Top-Up",
        "weekday": "Saturday",
        "duration": "55-65 min",
        "exercises": [
            {"name": "db_shoulder_press", "display": "DB Shoulder Press", "sets": 4, "reps": "8-10"},
            {"name": "lateral_raise_heavy", "display": "Lateral Raise (heavier)", "sets": 4, "reps": "10-12"},
            {"name": "lateral_raise_cable_drop", "display": "Cable Lateral Raise (drop set)", "sets": 3, "reps": "15-20"},
            {"name": "incline_db_fly", "display": "Incline DB Fly / Cable Fly", "sets": 3, "reps": "12-15"},
            {"name": "ss_curl_skull", "display": "SS: BB Curl / Skull Crushers", "sets": 3, "reps": "10-12"},
            {"name": "ss_incline_curl_oh_ext", "display": "SS: Incline Curl / OH Ext", "sets": 3, "reps": "12-15"},
            {"name": "db_shrug", "display": "Dumbbell Shrugs", "sets": 3, "reps": "10-12"},
            {"name": "neck_curl_ext", "display": "Neck Curl / Extension", "sets": 2, "reps": "15-20"},
            {"name": "farmers_carry", "display": "Farmer's Carry / Wrist Curls", "sets": 2, "reps": "30-40s"},
        ],
    },
}

DAY_WEEKDAY_MAP = {0: "day1_chest", 1: "day2_back", 4: "day3_legs", 5: "day4_shoulders"}


# ---------------------------------------------------------------------------
# Training Blocks
# ---------------------------------------------------------------------------

def _lookup_phase_for_date(date_str: str) -> dict | None:
    """Find the planned phase for a given date from the hardcoded timeline."""
    for phase in PHASE_TIMELINE:
        if phase["start"] <= date_str <= phase["end"]:
            return phase
    return None


def get_current_block() -> dict | None:
    """Get the current training block.

    1. Active override in DB → use it
    2. Active auto-created block for current phase → use it
    3. No block exists → auto-create from PHASE_TIMELINE
    """
    today_str = datetime.now().strftime("%Y-%m-%d")
    with SessionLocal() as session:
        # Check for override first
        override = (
            session.query(TrainingBlock)
            .filter_by(status="active", is_override=True)
            .first()
        )
        if override:
            return _block_to_dict(override)

        # Check for existing auto block
        existing = (
            session.query(TrainingBlock)
            .filter_by(status="active", is_override=False)
            .first()
        )
        if existing:
            # Check if it's still valid (date within range)
            if existing.end_date and today_str > existing.end_date:
                existing.status = "completed"
                session.commit()
            else:
                return _block_to_dict(existing)

        # Auto-create from timeline
        phase_info = _lookup_phase_for_date(today_str)
        if not phase_info:
            return None

        block = TrainingBlock(
            name=phase_info["name"],
            phase=phase_info["phase"],
            start_date=phase_info["start"],
            end_date=phase_info["end"],
            calorie_target=phase_info["cals"],
            protein_target=phase_info["protein"],
            fat_min=phase_info["fat_min"],
            fat_max=phase_info["fat_max"],
            is_override=False,
            status="active",
        )
        session.add(block)
        session.commit()
        return _block_to_dict(block)


def create_override_block(name: str, phase: str, start_date: str,
                          calorie_target: int = None, protein_target: int = None,
                          fat_min: int = None, fat_max: int = None,
                          notes: str = None) -> str:
    """Create a user-initiated override block. Completes any active block first."""
    with SessionLocal() as session:
        active = session.query(TrainingBlock).filter_by(status="active").all()
        for b in active:
            b.status = "completed"
            b.end_date = b.end_date or start_date

        block = TrainingBlock(
            name=name, phase=phase, start_date=start_date,
            calorie_target=calorie_target, protein_target=protein_target,
            fat_min=fat_min, fat_max=fat_max, notes=notes,
            is_override=True, status="active",
        )
        session.add(block)
        session.commit()
        return str(block.id)


def _block_to_dict(block: TrainingBlock) -> dict:
    return {
        "id": str(block.id),
        "name": block.name,
        "phase": block.phase,
        "start_date": block.start_date,
        "end_date": block.end_date,
        "calorie_target": block.calorie_target,
        "protein_target": block.protein_target,
        "fat_min": block.fat_min,
        "fat_max": block.fat_max,
        "is_override": block.is_override,
        "status": block.status,
    }


# ---------------------------------------------------------------------------
# Workout Sessions
# ---------------------------------------------------------------------------

def log_session(date: str, day_label: str, status: str = "completed",
                feedback: str = None, deviation_notes: str = None) -> str:
    """Create a workout session entry. Returns session ID."""
    block = get_current_block()
    block_id = block["id"] if block else None
    with SessionLocal() as session:
        ws = WorkoutSession(
            date=date, day_label=day_label, status=status,
            block_id=block_id, feedback=feedback,
            deviation_notes=deviation_notes,
        )
        session.add(ws)
        session.commit()
        return str(ws.id)


def get_session_for_date(date: str) -> dict | None:
    """Get a session for a specific date, if one exists."""
    with SessionLocal() as session:
        ws = session.query(WorkoutSession).filter_by(date=date).first()
        if not ws:
            return None
        return _session_to_dict(ws)


def get_or_create_session(date: str, day_label: str) -> dict:
    """Get today's session or create one (completed) for exercise logging."""
    existing = get_session_for_date(date)
    if existing:
        return existing
    sid = log_session(date, day_label, status="completed")
    return get_session_for_date(date)


def get_recent_sessions(limit: int = 8) -> list[dict]:
    """Get recent workout sessions ordered by date desc."""
    with SessionLocal() as session:
        rows = (
            session.query(WorkoutSession)
            .order_by(WorkoutSession.date.desc())
            .limit(limit)
            .all()
        )
        return [_session_to_dict(r) for r in rows]


def _session_to_dict(ws: WorkoutSession) -> dict:
    return {
        "id": str(ws.id),
        "date": ws.date,
        "day_label": ws.day_label,
        "status": ws.status,
        "feedback": ws.feedback,
        "deviation_notes": ws.deviation_notes,
    }


# ---------------------------------------------------------------------------
# Exercise Logs
# ---------------------------------------------------------------------------

def log_exercise(session_id: str, exercise: str, sets: int, reps: int,
                 weight_kg: float, rpe: int = None, notes: str = None) -> str:
    """Log a single exercise. Returns exercise log ID."""
    with SessionLocal() as session:
        el = ExerciseLog(
            session_id=session_id, exercise=exercise,
            sets=sets, reps=reps, weight_kg=weight_kg,
            rpe=rpe, notes=notes,
        )
        session.add(el)
        session.commit()
        return str(el.id)


def log_exercises_bulk(session_id: str, lifts: list[dict]) -> int:
    """Log multiple exercises at once. Returns count logged."""
    with SessionLocal() as session:
        for lift in lifts:
            el = ExerciseLog(
                session_id=session_id,
                exercise=lift["exercise"],
                sets=lift["sets"],
                reps=lift["reps"],
                weight_kg=lift["weight_kg"],
                rpe=lift.get("rpe"),
                notes=lift.get("notes"),
            )
            session.add(el)
        session.commit()
        return len(lifts)


def get_last_weight_for_exercise(exercise: str) -> dict | None:
    """Get the most recent logged weight/sets/reps for an exercise."""
    with SessionLocal() as session:
        el = (
            session.query(ExerciseLog)
            .filter_by(exercise=exercise)
            .order_by(ExerciseLog.created_at.desc())
            .first()
        )
        if not el:
            return None
        return {
            "exercise": el.exercise,
            "sets": el.sets,
            "reps": el.reps,
            "weight_kg": el.weight_kg,
            "date": el.created_at.strftime("%Y-%m-%d") if el.created_at else None,
        }


def get_exercise_history(exercise: str, limit: int = 10) -> list[dict]:
    """Get recent history for an exercise."""
    with SessionLocal() as session:
        rows = (
            session.query(ExerciseLog)
            .filter_by(exercise=exercise)
            .order_by(ExerciseLog.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "sets": r.sets, "reps": r.reps, "weight_kg": r.weight_kg,
                "rpe": r.rpe, "date": r.created_at.strftime("%Y-%m-%d") if r.created_at else None,
            }
            for r in rows
        ]


# ---------------------------------------------------------------------------
# Workout Modifications
# ---------------------------------------------------------------------------

def create_modification(exercise: str, modification_type: str, detail: str,
                        reason: str = None, valid_from: str = None,
                        valid_until: str = None) -> str:
    """Create a workout modification. Returns modification ID."""
    if not valid_from:
        valid_from = datetime.now().strftime("%Y-%m-%d")
    with SessionLocal() as session:
        mod = WorkoutModification(
            exercise=exercise, modification_type=modification_type,
            detail=detail, reason=reason,
            valid_from=valid_from, valid_until=valid_until,
            status="active",
        )
        session.add(mod)
        session.commit()
        return str(mod.id)


def get_active_modifications() -> list[dict]:
    """Get all active (non-expired, non-cancelled) modifications."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    with SessionLocal() as session:
        rows = (
            session.query(WorkoutModification)
            .filter_by(status="active")
            .all()
        )
        result = []
        for m in rows:
            # Auto-expire if past valid_until
            if m.valid_until and today_str > m.valid_until:
                m.status = "expired"
                continue
            # Only include if valid_from has arrived
            if m.valid_from <= today_str:
                result.append({
                    "id": str(m.id),
                    "exercise": m.exercise,
                    "modification_type": m.modification_type,
                    "detail": m.detail,
                    "reason": m.reason,
                    "valid_from": m.valid_from,
                    "valid_until": m.valid_until,
                })
        session.commit()  # persist any auto-expirations
        return result


# ---------------------------------------------------------------------------
# Weigh-Ins
# ---------------------------------------------------------------------------

def log_weigh_in(date: str, weight_kg: float, notes: str = None) -> str:
    """Log a weigh-in. Returns ID."""
    block = get_current_block()
    block_id = block["id"] if block else None
    with SessionLocal() as session:
        wi = WeighIn(date=date, weight_kg=weight_kg, block_id=block_id, notes=notes)
        session.add(wi)
        session.commit()
        return str(wi.id)


def get_recent_weigh_ins(limit: int = 8) -> list[dict]:
    """Get recent weigh-ins (default ~2 months at weekly pace)."""
    with SessionLocal() as session:
        rows = (
            session.query(WeighIn)
            .order_by(WeighIn.date.desc())
            .limit(limit)
            .all()
        )
        return [{"date": r.date, "weight_kg": r.weight_kg, "notes": r.notes} for r in rows]


def get_weight_trend() -> dict:
    """Calculate weight trend from recent weigh-ins."""
    weigh_ins = get_recent_weigh_ins(limit=8)
    if not weigh_ins:
        return {"current": None, "avg_4wk": None, "direction": "unknown", "rate_per_week": None}

    current = weigh_ins[0]["weight_kg"]
    last_date = weigh_ins[0]["date"]

    # 4-week average (last 4 entries at weekly pace)
    last_4 = weigh_ins[:4]
    avg_4wk = sum(w["weight_kg"] for w in last_4) / len(last_4) if last_4 else None

    # Rate calculation (if we have at least 2 data points)
    rate_per_week = None
    direction = "stable"
    if len(weigh_ins) >= 2:
        oldest = weigh_ins[-1]
        weight_diff = current - oldest["weight_kg"]
        try:
            days_diff = (datetime.strptime(last_date, "%Y-%m-%d") -
                         datetime.strptime(oldest["date"], "%Y-%m-%d")).days
            if days_diff > 0:
                rate_per_week = round(weight_diff / (days_diff / 7), 2)
                if rate_per_week > 0.05:
                    direction = "up"
                elif rate_per_week < -0.05:
                    direction = "down"
        except (ValueError, ZeroDivisionError):
            pass

    return {
        "current": current,
        "last_date": last_date,
        "avg_4wk": round(avg_4wk, 1) if avg_4wk else None,
        "direction": direction,
        "rate_per_week": rate_per_week,
    }


# ---------------------------------------------------------------------------
# Nutrition (monthly)
# ---------------------------------------------------------------------------

def log_monthly_nutrition(month: str, avg_calories: int = None,
                          avg_protein_g: int = None, avg_carbs_g: int = None,
                          avg_fat_g: int = None, notes: str = None) -> str:
    """Log or update monthly nutrition. Upserts on month. Returns ID."""
    block = get_current_block()
    block_id = block["id"] if block else None
    with SessionLocal() as session:
        existing = session.query(NutritionLog).filter_by(month=month).first()
        if existing:
            if avg_calories is not None:
                existing.avg_calories = avg_calories
            if avg_protein_g is not None:
                existing.avg_protein_g = avg_protein_g
            if avg_carbs_g is not None:
                existing.avg_carbs_g = avg_carbs_g
            if avg_fat_g is not None:
                existing.avg_fat_g = avg_fat_g
            if notes is not None:
                existing.notes = notes
            existing.block_id = block_id
            session.commit()
            return str(existing.id)

        nl = NutritionLog(
            month=month, avg_calories=avg_calories,
            avg_protein_g=avg_protein_g, avg_carbs_g=avg_carbs_g,
            avg_fat_g=avg_fat_g, block_id=block_id, notes=notes,
        )
        session.add(nl)
        session.commit()
        return str(nl.id)


def get_recent_nutrition(limit: int = 3) -> list[dict]:
    """Get recent monthly nutrition logs."""
    with SessionLocal() as session:
        rows = (
            session.query(NutritionLog)
            .order_by(NutritionLog.month.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "month": r.month, "avg_calories": r.avg_calories,
                "avg_protein_g": r.avg_protein_g, "avg_carbs_g": r.avg_carbs_g,
                "avg_fat_g": r.avg_fat_g, "notes": r.notes,
            }
            for r in rows
        ]


# ---------------------------------------------------------------------------
# Sleep
# ---------------------------------------------------------------------------

def log_sleep(date: str, hours: float, notes: str = None) -> str:
    """Log sleep for a date. Upserts. Returns ID."""
    with SessionLocal() as session:
        existing = session.query(SleepLog).filter_by(date=date).first()
        if existing:
            existing.hours = hours
            if notes is not None:
                existing.notes = notes
            session.commit()
            return str(existing.id)

        sl = SleepLog(date=date, hours=hours, notes=notes)
        session.add(sl)
        session.commit()
        return str(sl.id)


def get_sleep_average(days: int = 7) -> dict:
    """Get sleep average over last N logged days."""
    with SessionLocal() as session:
        rows = (
            session.query(SleepLog)
            .order_by(SleepLog.date.desc())
            .limit(days)
            .all()
        )
        if not rows:
            return {"avg": None, "count": 0, "last": None}
        avg = round(sum(r.hours for r in rows) / len(rows), 1)
        return {
            "avg": avg,
            "count": len(rows),
            "last": rows[0].hours,
            "last_date": rows[0].date,
            "below_7": avg < 7.0,
        }


# ---------------------------------------------------------------------------
# Deload Tracker
# ---------------------------------------------------------------------------

def get_active_deload_cycle() -> dict | None:
    """Get the current active deload cycle."""
    with SessionLocal() as session:
        dc = session.query(DeloadTracker).filter_by(status="active").first()
        if not dc:
            return None
        return {
            "id": str(dc.id),
            "cycle_start_date": dc.cycle_start_date,
            "weeks_completed": dc.weeks_completed,
            "deload_done": dc.deload_done,
        }


def start_deload_cycle(start_date: str) -> str:
    """Start a new deload cycle, completing any active one. Returns cycle ID."""
    with SessionLocal() as session:
        active = session.query(DeloadTracker).filter_by(status="active").first()
        if active:
            active.status = "completed"
        dc = DeloadTracker(cycle_start_date=start_date, weeks_completed=0, status="active")
        session.add(dc)
        session.commit()
        return str(dc.id)


def increment_deload_week() -> dict | None:
    """Increment weeks_completed on active cycle. Returns updated cycle."""
    with SessionLocal() as session:
        dc = session.query(DeloadTracker).filter_by(status="active").first()
        if not dc:
            return None
        dc.weeks_completed += 1
        session.commit()
        return {
            "weeks_completed": dc.weeks_completed,
            "deload_due": dc.weeks_completed >= 8,
        }


def complete_deload() -> bool:
    """Mark deload as done and start fresh cycle."""
    with SessionLocal() as session:
        dc = session.query(DeloadTracker).filter_by(status="active").first()
        if not dc:
            return False
        dc.deload_done = True
        dc.status = "completed"
        # Start a new cycle
        new_dc = DeloadTracker(
            cycle_start_date=datetime.now().strftime("%Y-%m-%d"),
            weeks_completed=0, status="active",
        )
        session.add(new_dc)
        session.commit()
        return True


# ---------------------------------------------------------------------------
# Formatting (for prompt injection and query responses)
# ---------------------------------------------------------------------------

def _get_todays_day_label() -> str | None:
    """Get today's day label from the weekday map, or None if rest day."""
    weekday = datetime.now().weekday()
    return DAY_WEEKDAY_MAP.get(weekday)


def format_fitness_summary() -> str:
    """Build the fitness context section for the system prompt."""
    lines = []

    # Current block/phase
    block = get_current_block()
    if block:
        fat_str = f"{block['fat_min']}-{block['fat_max']}g fat" if block['fat_min'] else ""
        lines.append(f"**Phase:** {block['name']} ({block['phase']}) — {block['start_date']} to {block['end_date'] or '?'}")
        parts = []
        if block["calorie_target"]:
            parts.append(f"{block['calorie_target']} kcal")
        if block["protein_target"]:
            parts.append(f"{block['protein_target']}g protein")
        if fat_str:
            parts.append(fat_str)
        if parts:
            lines.append(f"  Targets: {' | '.join(parts)}")
    else:
        lines.append("**Phase:** No active training block (between phases or pre-program)")

    # Today's workout
    day_label = _get_todays_day_label()
    if day_label and day_label in TRAINING_SPLIT:
        day = TRAINING_SPLIT[day_label]
        lines.append(f"**Today:** {day['label']} ({day['weekday']})")
        # Show each exercise with last-known weight
        mods = get_active_modifications()
        mod_map = {m["exercise"]: m for m in mods}
        for ex in day["exercises"]:
            last = get_last_weight_for_exercise(ex["name"])
            weight_str = f"{last['weight_kg']}kg ({last['sets']}x{last['reps']})" if last else "no data"
            mod_note = ""
            if ex["name"] in mod_map:
                mod_note = f" [MOD: {mod_map[ex['name']]['detail']}]"
            lines.append(f"  {ex['display']}: {weight_str} — target {ex['reps']}{mod_note}")
    else:
        # Rest day — find next session
        today_wd = datetime.now().weekday()
        for offset in range(1, 8):
            next_wd = (today_wd + offset) % 7
            if next_wd in DAY_WEEKDAY_MAP:
                next_label = DAY_WEEKDAY_MAP[next_wd]
                next_day = TRAINING_SPLIT[next_label]
                lines.append(f"**Today:** Rest day. Next: {next_day['label']} ({next_day['weekday']})")
                break

    # Active modifications
    mods = get_active_modifications()
    if mods:
        mod_strs = []
        for m in mods:
            until = f"until {m['valid_until']}" if m["valid_until"] else "permanent"
            mod_strs.append(f"{m['exercise']} → {m['detail']} ({until})")
        lines.append(f"**Active Mods:** {'; '.join(mod_strs)}")

    # Weight trend
    trend = get_weight_trend()
    if trend["current"]:
        weight_parts = [f"{trend['current']}kg ({trend['last_date']})"]
        if trend["avg_4wk"]:
            weight_parts.append(f"4-wk avg: {trend['avg_4wk']}kg")
        if trend["rate_per_week"] is not None:
            sign = "+" if trend["rate_per_week"] > 0 else ""
            weight_parts.append(f"{sign}{trend['rate_per_week']}kg/wk")
        # Phase target
        if block:
            for pt in PHASE_TIMELINE:
                if pt["name"] == block["name"] and "target" not in pt:
                    break
            # Target from timeline (heuristic: show start→end weight)
        lines.append(f"**Weight:** {' | '.join(weight_parts)}")

    # Sleep
    sleep = get_sleep_average()
    if sleep["avg"]:
        warning = " ⚠ below 7h" if sleep["below_7"] else ""
        lines.append(f"**Sleep:** 7-day avg: {sleep['avg']}h{warning}")

    # Deload
    deload = get_active_deload_cycle()
    if deload:
        lines.append(f"**Deload:** Week {deload['weeks_completed']} of 8")

    # Recent sessions (last 4)
    sessions = get_recent_sessions(limit=4)
    if sessions:
        session_strs = []
        for s in sessions:
            day_info = TRAINING_SPLIT.get(s["day_label"], {})
            day_short = day_info.get("weekday", s["day_label"])[:3]
            status_icon = "✓" if s["status"] == "completed" else s["status"]
            extra = f": {s['feedback'][:30]}" if s.get("feedback") else ""
            session_strs.append(f"{day_short} {s['date'][-5:]} {status_icon}{extra}")
        lines.append(f"**Recent:** {' | '.join(session_strs)}")

    return "\n".join(lines)


def format_fitness_detail() -> str:
    """Detailed fitness status for query_fitness responses."""
    lines = [format_fitness_summary(), ""]

    # Nutrition
    nutrition = get_recent_nutrition(limit=3)
    if nutrition:
        lines.append("**Nutrition (monthly):**")
        for n in nutrition:
            parts = [n["month"]]
            if n["avg_calories"]:
                parts.append(f"{n['avg_calories']} kcal")
            if n["avg_protein_g"]:
                parts.append(f"{n['avg_protein_g']}g protein")
            if n["avg_fat_g"]:
                parts.append(f"{n['avg_fat_g']}g fat")
            lines.append(f"  {' | '.join(parts)}")

    # Recent sessions with more detail
    sessions = get_recent_sessions(limit=8)
    if sessions:
        lines.append("\n**Session History:**")
        for s in sessions:
            day_info = TRAINING_SPLIT.get(s["day_label"], {})
            label = day_info.get("label", s["day_label"])
            status_str = s["status"]
            line = f"  {s['date']} — {label} [{status_str}]"
            if s.get("feedback"):
                line += f" — {s['feedback']}"
            if s.get("deviation_notes"):
                line += f" (deviation: {s['deviation_notes']})"
            lines.append(line)

    return "\n".join(lines)


def get_fitness_prompt() -> str:
    """Static fitness rules for the system prompt."""
    return """
## Fitness Program Rules
Training split: Mon (Chest+Delts), Tue (Back+Biceps+Yoke), Fri (Legs+Abs), Sat (Shoulders+Arms)
Pre-workout: Thoracic foam roll 60s, band pull-aparts 2x15, wall slides 2x10

Progression: When Jason hits the top of the rep range for all sets, suggest adding weight next session.
  Barbell exercises: +2.5kg. Dumbbells: next available increment. Cables: +1 plate.
Deload: Every 8 weeks, drop all weights 10%, focus on form. Non-negotiable.
Stalled lift: Check sleep first (7-day avg < 7h?), then nutrition compliance, then recovery. Change program last.

Bulk rules: +300-400 kcal surplus. Max 0.75kg/wk gain. Protein 170-175g. Fat 60-80g.
Mini-cut rules: 3 weeks max. -500-600 kcal deficit. Protein 180-185g. Keep training intensity.
Final cut rules: -400-500 kcal. Protein 185g+. Max 0.5kg/wk loss. Refeed every 10-14 days.

Fallback: 3 days (drop Sat), 2 days (Day 1 + Day 3 only), extended absence (deload on return if 2+ weeks missed).

Exception-based: Assume gym sessions completed as planned. Only log when Jason mentions specific numbers, deviations, or missed sessions. Silence = compliance.
"""
