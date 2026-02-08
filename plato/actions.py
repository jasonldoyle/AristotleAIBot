"""
Action processing for Plato bot.
Each action corresponds to a JSON block Claude returns in its response.
"""

from datetime import datetime, timedelta
from plato.config import logger
from plato.db import (
    get_project_by_slug, log_work, create_project, add_soul_doc_entry,
    add_project_goal, mark_goal_achieved, update_project, add_pattern,
    log_fitness_exercises, store_pending_plan, get_pending_plan,
    clear_pending_plan, store_schedule_events, update_schedule_event,
    get_planned_events_for_date, mark_evening_audrey, park_idea, resolve_idea,
    parse_revolut_csv, parse_aib_csv, import_transactions,
    get_monthly_summary, check_budget_alerts, set_budget_limit,
    # New fitness imports
    log_daily, log_training_session, log_missed_session,
    confirm_progression, parse_mfp_diary, import_nutrition,
    create_training_block, generate_weekly_summary, generate_block_summary,
    log_progress_photos, get_all_lift_latest, MAIN_LIFTS,
    add_fitness_goal, get_fitness_goals, achieve_fitness_goal,
    revise_fitness_goal, generate_block_workouts,
    calculate_block_dates, get_phase_for_month, get_nutrition_for_phase, plan_next_block,
)
from plato_calendar import (
    get_calendar_service, clear_plato_events, create_weekly_events,
    cancel_evening_events, create_event
)


COLOR_MAP = {
    "cfa": "9", "nitrogen": "10", "glowbook": "6", "plato": "7",
    "leetcode": "3", "rest": "8", "exercise": "2", "personal": "4",
    "citco": "1", "audrey": "11",
}


def process_action(action_data: dict, raw_message: str) -> str | None:
    """Process a JSON action and return a status message if needed."""
    action = action_data.get("action")

    try:
        if action == "log":
            return _process_log(action_data, raw_message)
        elif action == "create_project":
            return _process_create_project(action_data)
        elif action == "add_soul":
            return _process_add_soul(action_data)
        elif action == "add_goal":
            return _process_add_goal(action_data)
        elif action == "achieve_goal":
            return _process_achieve_goal(action_data)
        elif action == "update_project":
            return _process_update_project(action_data)
        elif action == "add_pattern":
            return _process_add_pattern(action_data)
        elif action == "plan_week":
            return process_plan_week(action_data)
        elif action == "log_fitness":
            count = log_fitness_exercises(action_data.get("exercises", []))
            return f"💪 Logged {count} exercises."
        elif action == "audrey_time":
            return process_audrey_time(action_data)
        elif action == "add_event":
            return process_add_event(action_data)
        elif action == "check_in":
            return process_check_in(action_data)
        elif action == "park_idea":
            idea = park_idea(
                idea=action_data["idea"],
                context=action_data.get("context")
            )
            eligible = idea["eligible_date"]
            return f"💡 Parked: \"{action_data['idea']}\"\nEligible for review: {eligible}"
        elif action == "resolve_idea":
            success = resolve_idea(
                idea_fragment=action_data["idea_fragment"],
                status=action_data["status"],
                notes=action_data.get("notes")
            )
            if success:
                return f"{'✅' if action_data['status'] == 'approved' else '❌'} Idea resolved: {action_data['status']}"
            else:
                return f"⚠️ Couldn't find parked idea matching '{action_data['idea_fragment']}'"
        elif action == "finance_review":
            return process_finance_review(action_data)
        elif action == "set_budget":
            return process_set_budget(action_data)

        # ===== NEW FITNESS ACTIONS =====
        elif action == "daily_log":
            return process_daily_log(action_data)
        elif action == "log_workout":
            return process_log_workout(action_data)
        elif action == "missed_workout":
            return process_missed_workout(action_data)
        elif action == "confirm_lift":
            return process_confirm_lift(action_data)
        elif action == "weekly_fitness_summary":
            return process_weekly_fitness_summary(action_data)
        elif action == "block_summary":
            return process_block_summary(action_data)
        elif action == "create_block":
            return process_create_block(action_data)
        elif action == "plan_next_block":
            return process_plan_next_block(action_data)
        elif action == "progress_photos":
            return process_progress_photos(action_data)
        elif action == "add_fitness_goal":
            return process_add_fitness_goal(action_data)
        elif action == "achieve_fitness_goal":
            return process_achieve_fitness_goal(action_data)
        elif action == "revise_fitness_goal":
            return process_revise_fitness_goal(action_data)

        return None

    except Exception as e:
        logger.error(f"Action processing error: {e}")
        return f"⚠️ Error processing action: {str(e)}"


# ============== INDIVIDUAL ACTION PROCESSORS ==============

def _process_log(action_data: dict, raw_message: str) -> str | None:
    project = get_project_by_slug(action_data["project_slug"])
    if project:
        log_work(
            project_id=project["id"],
            summary=action_data["summary"],
            duration_mins=action_data.get("duration_mins"),
            blockers=action_data.get("blockers"),
            tags=action_data.get("tags", []),
            mood=action_data.get("mood"),
            raw_message=raw_message
        )
        logger.info(f"Logged work for {action_data['project_slug']}")
        return None
    return f"⚠️ Project '{action_data['project_slug']}' not found."


def _process_create_project(action_data: dict) -> str | None:
    create_project(
        name=action_data["name"],
        slug=action_data["slug"],
        intent=action_data["intent"]
    )
    logger.info(f"Created project: {action_data['slug']}")
    return None


def _process_add_soul(action_data: dict) -> str | None:
    add_soul_doc_entry(
        content=action_data["content"],
        category=action_data["category"],
        trigger=action_data.get("trigger", "Conversation")
    )
    logger.info(f"Added soul doc entry: {action_data['category']}")
    return None


def _process_add_goal(action_data: dict) -> str | None:
    project = get_project_by_slug(action_data["project_slug"])
    if project:
        add_project_goal(
            project_id=project["id"],
            timeframe=action_data["timeframe"],
            goal_text=action_data["goal_text"],
            target_date=action_data.get("target_date")
        )
        logger.info(f"Added {action_data['timeframe']} goal to {action_data['project_slug']}")
        return None
    return f"⚠️ Project '{action_data['project_slug']}' not found."


def _process_achieve_goal(action_data: dict) -> str | None:
    success = mark_goal_achieved(
        project_slug=action_data["project_slug"],
        goal_text_fragment=action_data["goal_fragment"]
    )
    if success:
        logger.info(f"Marked goal achieved for {action_data['project_slug']}")
        return None
    return f"⚠️ Couldn't find matching goal for '{action_data['goal_fragment']}'."


def _process_update_project(action_data: dict) -> str | None:
    success = update_project(
        slug=action_data["slug"],
        updates=action_data["updates"]
    )
    if success:
        logger.info(f"Updated project: {action_data['slug']}")
        return None
    return f"⚠️ Project '{action_data['slug']}' not found."


def _process_add_pattern(action_data: dict) -> str | None:
    project_id = None
    if action_data.get("project_slug"):
        project = get_project_by_slug(action_data["project_slug"])
        if project:
            project_id = project["id"]

    add_pattern(
        pattern_type=action_data["pattern_type"],
        description=action_data["description"],
        project_id=project_id
    )
    logger.info(f"Added pattern: {action_data['pattern_type']}")
    return None


# ============== CALENDAR ACTIONS ==============

def process_plan_week(action_data: dict) -> str:
    try:
        events = action_data.get("events", [])
        if not events:
            return "⚠️ No events in schedule."

        store_pending_plan(events)

        by_date = {}
        for e in events:
            d = e["date"]
            if d not in by_date:
                by_date[d] = []
            by_date[d].append(f"  {e['start']}-{e['end']}: {e['title']}")

        summary = "📋 PROPOSED SCHEDULE:\n\n"
        for date in sorted(by_date.keys()):
            day_name = datetime.strptime(date, "%Y-%m-%d").strftime("%A %b %d")
            summary += f"{day_name}:\n"
            summary += "\n".join(by_date[date]) + "\n\n"

        summary += f"Total: {len(events)} blocks.\n"
        summary += "Say 'approve' to push to calendar, or tell me what to change."
        return summary

    except Exception as e:
        logger.error(f"Plan week error: {e}")
        return f"⚠️ Plan error: {e}"


def process_approve_plan() -> str:
    try:
        events = get_pending_plan()
        if not events:
            return "⚠️ No pending plan to approve. Say 'plan my week' first."

        service = get_calendar_service()
        first_date = datetime.strptime(events[0]["date"], "%Y-%m-%d")
        week_start = first_date - timedelta(days=first_date.weekday())

        cleared = clear_plato_events(service, week_start)
        created = create_weekly_events(service, events)
        stored = store_schedule_events(events)
        clear_pending_plan()

        return f"📅 Approved! Scheduled {created} events (cleared {cleared} old ones). Tracking {stored} blocks."

    except Exception as e:
        logger.error(f"Approve plan error: {e}")
        return f"⚠️ Error pushing plan: {e}"


def process_audrey_time(action_data: dict) -> str:
    try:
        date_str = action_data.get("date", datetime.now().strftime("%Y-%m-%d"))
        from_time = action_data.get("from_time", "18:00")

        service = get_calendar_service()
        cancelled = cancel_evening_events(service, date_str, from_time)
        affected = mark_evening_audrey(date_str, from_time)

        if not cancelled and not affected:
            return "No planned blocks to cancel for tonight."

        bumped_titles = [e["title"] for e in cancelled]
        return f"💕 Audrey time activated. Cancelled {len(cancelled)} blocks: {', '.join(bumped_titles)}"

    except Exception as e:
        logger.error(f"Audrey time error: {e}")
        return f"⚠️ Error activating Audrey time: {e}"


def process_add_event(action_data: dict) -> str:
    try:
        service = get_calendar_service()
        date_str = action_data["date"]
        start = action_data["start"]
        end = action_data["end"]
        title = action_data["title"]
        category = action_data.get("category", "personal")
        description = action_data.get("description")

        create_event(
            service, date_str=date_str, start_time=start, end_time=end,
            title=title, description=description,
            color_id=COLOR_MAP.get(category)
        )
        return f"📌 Added: {title} on {date_str} {start}-{end}"

    except Exception as e:
        logger.error(f"Add event error: {e}")
        return f"⚠️ Error adding event: {e}"


def process_check_in(action_data: dict) -> str:
    try:
        event_id = action_data.get("event_id")
        status = action_data.get("status", "completed")
        actual_summary = action_data.get("actual_summary")
        gap_reason = action_data.get("gap_reason")

        if event_id:
            update_schedule_event(event_id, status, actual_summary, gap_reason)
            return f"✅ Checked in: {status}"
        else:
            today = datetime.now().strftime("%Y-%m-%d")
            events = get_planned_events_for_date(today)
            now = datetime.now().strftime("%H:%M")

            recent = None
            for e in events:
                if e["end_time"] <= now and e["status"] == "planned":
                    recent = e

            if recent:
                update_schedule_event(recent["id"], status, actual_summary, gap_reason)
                return f"✅ Checked in for '{recent['title']}': {status}"
            else:
                return "No recent planned block found to check in against."

    except Exception as e:
        logger.error(f"Check-in error: {e}")
        return f"⚠️ Check-in error: {e}"


# ============== FINANCE ACTIONS ==============

def process_import_csv(csv_content: str, source: str) -> str:
    try:
        if source == "revolut":
            transactions = parse_revolut_csv(csv_content)
        elif source == "aib":
            transactions = parse_aib_csv(csv_content)
        else:
            return f"⚠️ Unknown source: {source}"

        if not transactions:
            return "⚠️ No transactions found in the CSV."

        stats = import_transactions(transactions)

        income = sum(t["amount"] for t in transactions if t["amount"] > 0 and not t["is_transfer"])
        spending = sum(abs(t["amount"]) for t in transactions if t["amount"] < 0 and not t["is_transfer"])

        msg = f"💰 Imported {stats['imported']} transactions from {source.upper()}"
        if stats["skipped"] > 0:
            msg += f" ({stats['skipped']} duplicates skipped)"
        msg += f"\n📊 Income: €{income:,.2f} | Spending: €{spending:,.2f}"

        now = datetime.now()
        alerts = check_budget_alerts(now.year, now.month)
        if alerts:
            msg += "\n\n🚨 Budget alerts:"
            for a in alerts:
                icon = "🔴" if a["status"] == "over" else "🟡"
                msg += f"\n  {icon} {a['category']}: €{a['spent']:.2f} / €{a['limit']:.2f} ({a['pct']}%)"

        return msg

    except Exception as e:
        logger.error(f"CSV import error: {e}")
        return f"⚠️ Error importing CSV: {e}"


def process_finance_review(action_data: dict) -> str:
    try:
        year = action_data.get("year", datetime.now().year)
        month = action_data.get("month", datetime.now().month)

        summary = get_monthly_summary(year, month)

        msg = f"💰 FINANCE REVIEW — {summary['month']}\n\n"
        msg += f"Income: €{summary['total_income']:,.2f}\n"
        msg += f"Spending: €{summary['total_spending']:,.2f}\n"
        msg += f"Net: €{summary['net']:,.2f}\n"
        msg += f"Savings rate: {summary['savings_rate']}%\n"
        msg += f"Transactions: {summary['transaction_count']}\n\n"

        if summary["by_category"]:
            msg += "Spending by category:\n"
            for cat, amount in summary["by_category"].items():
                msg += f"  • {cat}: €{amount:,.2f}\n"

        alerts = check_budget_alerts(year, month)
        if alerts:
            msg += "\n🚨 Budget alerts:\n"
            for a in alerts:
                icon = "🔴" if a["status"] == "over" else "🟡"
                msg += f"  {icon} {a['category']}: €{a['spent']:.2f} / €{a['limit']:.2f} ({a['pct']}%)\n"

        return msg

    except Exception as e:
        logger.error(f"Finance review error: {e}")
        return f"⚠️ Error generating finance review: {e}"


def process_set_budget(action_data: dict) -> str:
    try:
        category = action_data["category"]
        limit = float(action_data["monthly_limit"])
        set_budget_limit(category, limit)
        return f"💰 Budget set: {category} → €{limit:,.2f}/month"
    except Exception as e:
        logger.error(f"Set budget error: {e}")
        return f"⚠️ Error setting budget: {e}"


# ============== FITNESS ACTIONS ==============

def process_daily_log(action_data: dict) -> str:
    """Log daily check-in: weight, skincare, health, steps, cycling."""
    try:
        date = action_data.get("date", datetime.now().strftime("%Y-%m-%d"))
        kwargs = {}

        if "weight_kg" in action_data:
            kwargs["weight_kg"] = float(action_data["weight_kg"])
        if "steps" in action_data:
            kwargs["steps"] = int(action_data["steps"])
        if "skincare_am" in action_data:
            kwargs["skincare_am"] = action_data["skincare_am"]
        if "skincare_pm" in action_data:
            kwargs["skincare_pm"] = action_data["skincare_pm"]
        if "skincare_notes" in action_data:
            kwargs["skincare_notes"] = action_data["skincare_notes"]
        if "cycling_scheduled" in action_data:
            kwargs["cycling_scheduled"] = action_data["cycling_scheduled"]
        if "cycling_completed" in action_data:
            kwargs["cycling_completed"] = action_data["cycling_completed"]
        if "cycling_notes" in action_data:
            kwargs["cycling_notes"] = action_data["cycling_notes"]
        if "urticaria_severity" in action_data:
            kwargs["urticaria_severity"] = action_data["urticaria_severity"]
        if "breakout_severity" in action_data:
            kwargs["breakout_severity"] = action_data["breakout_severity"]
        if "breakout_location" in action_data:
            kwargs["breakout_location"] = action_data["breakout_location"]
        if "health_notes" in action_data:
            kwargs["health_notes"] = action_data["health_notes"]
        if "sleep_hours" in action_data:
            kwargs["sleep_hours"] = float(action_data["sleep_hours"])

        log_daily(date=date, **kwargs)

        # Build confirmation message
        parts = []
        if "weight_kg" in kwargs:
            parts.append(f"⚖️ {kwargs['weight_kg']}kg")
        if "steps" in kwargs:
            parts.append(f"👟 {kwargs['steps']:,} steps")
        if "skincare_am" in kwargs and not kwargs["skincare_am"]:
            parts.append("☀️ Skincare AM missed")
        if "skincare_pm" in kwargs and not kwargs["skincare_pm"]:
            parts.append("🌙 Skincare PM missed")
        if "cycling_completed" in kwargs and not kwargs["cycling_completed"]:
            parts.append(f"🚴 Cycling missed: {kwargs.get('cycling_notes', 'no reason')}")
        if "urticaria_severity" in kwargs:
            parts.append(f"🔴 Urticaria: {kwargs['urticaria_severity']}/10")
        if "breakout_severity" in kwargs:
            parts.append(f"😤 Breakout: {kwargs['breakout_severity']}/10")
        if "sleep_hours" in kwargs:
            parts.append(f"😴 {kwargs['sleep_hours']}h sleep")

        if parts:
            return "📋 Daily log updated:\n" + "\n".join(f"  {p}" for p in parts)
        return "📋 Daily log updated."

    except Exception as e:
        logger.error(f"Daily log error: {e}")
        return f"⚠️ Error logging daily: {e}"


def process_log_workout(action_data: dict) -> str:
    """Log a full training session with exercises and progressive overload tracking."""
    try:
        session_type = action_data["session_type"]
        exercises = action_data.get("exercises", [])
        date = action_data.get("date", datetime.now().strftime("%Y-%m-%d"))
        feedback = action_data.get("feedback")
        duration = action_data.get("duration_mins")

        result = log_training_session(
            session_type=session_type,
            exercises=exercises,
            date=date,
            feedback=feedback,
            duration_mins=duration,
        )

        msg = f"💪 {result['session']['session_type']} logged — {result['exercise_count']} exercises"
        if duration:
            msg += f" ({duration} mins)"

        # Report main lift progressions
        for prog in result["main_lift_progressions"]:
            if prog["hit_target"]:
                msg += f"\n  🔥 {prog['lift']}: {prog['weight']}kg × {prog['sets']}×{prog['reps']} — HIT TARGET!"
                msg += f"\n  📈 Ready to move to {prog['next_weight']}kg. Confirm?"
            else:
                msg += f"\n  🏋️ {prog['lift']}: {prog['weight']}kg × {prog['sets']}×{prog['reps']}"

        if feedback:
            msg += f"\n  💬 {feedback}"

        return msg

    except Exception as e:
        logger.error(f"Log workout error: {e}")
        return f"⚠️ Error logging workout: {e}"


def process_missed_workout(action_data: dict) -> str:
    """Log a missed training session."""
    try:
        session_type = action_data["session_type"]
        reason = action_data.get("reason")
        date = action_data.get("date", datetime.now().strftime("%Y-%m-%d"))

        result = log_missed_session(session_type=session_type, date=date, reason=reason)
        msg = f"❌ Missed: {result['session_type']}"
        if reason:
            msg += f" — {reason}"
        return msg

    except Exception as e:
        logger.error(f"Missed workout error: {e}")
        return f"⚠️ Error logging missed workout: {e}"


def process_confirm_lift(action_data: dict) -> str:
    """Confirm progression for a main lift."""
    try:
        lift_key = action_data["lift_key"]
        return confirm_progression(lift_key)
    except Exception as e:
        logger.error(f"Confirm lift error: {e}")
        return f"⚠️ Error confirming lift: {e}"


def process_import_mfp(text: str) -> str:
    """Parse and import MFP printable diary text."""
    try:
        entries = parse_mfp_diary(text)
        if not entries:
            return "⚠️ No nutrition data found. Make sure it's the MFP printable diary format."

        stats = import_nutrition(entries)

        # Calculate averages
        avg_cals = round(sum(e["calories"] for e in entries) / len(entries))
        avg_protein = round(sum(e["protein_g"] for e in entries) / len(entries))
        date_range = f"{entries[0]['date']} to {entries[-1]['date']}"

        msg = f"🍽️ Imported {stats['imported']} days of nutrition ({date_range})"
        if stats["skipped"] > 0:
            msg += f" ({stats['skipped']} errors)"
        msg += f"\n📊 Avg: {avg_cals} cal | {avg_protein}g protein"

        # Flag days below targets
        low_cal = [e for e in entries if e["calories"] < 2800]
        low_protein = [e for e in entries if e["protein_g"] < 160]
        if low_cal:
            msg += f"\n⚠️ {len(low_cal)} days under 2800 cal"
        if low_protein:
            msg += f"\n⚠️ {len(low_protein)} days under 160g protein"

        return msg

    except Exception as e:
        logger.error(f"MFP import error: {e}")
        return f"⚠️ Error importing MFP data: {e}"


def process_weekly_fitness_summary(action_data: dict) -> str:
    """Generate weekly fitness summary."""
    try:
        week_start = action_data.get("week_start")
        summary = generate_weekly_summary(week_start)

        t = summary["training"]
        w = summary["weight"]
        n = summary["nutrition"]
        c = summary["cycling"]
        s = summary["skincare"]
        h = summary["health"]

        msg = f"📊 WEEKLY FITNESS SUMMARY — {summary['week']}\n\n"

        # Training
        msg += f"🏋️ Training: {t['completed']}/{t['target']} sessions\n"
        for sess in t["sessions"]:
            msg += f"  ✅ {sess['date']}: {sess['type']}\n"
        for miss in t["missed"]:
            msg += f"  ❌ {miss['type']}: {miss.get('reason', 'no reason')}\n"

        # Weight
        if w["start"] and w["end"]:
            change = f"+{w['change']}" if w["change"] and w["change"] > 0 else str(w["change"])
            msg += f"\n⚖️ Weight: {w['start']}kg → {w['end']}kg ({change}kg)\n"
        elif w["end"]:
            msg += f"\n⚖️ Weight: {w['end']}kg\n"

        # Nutrition
        if n["avg_calories"]:
            msg += f"\n🍽️ Nutrition: avg {n['avg_calories']} cal / {n['avg_protein']}g protein"
            msg += f" ({n['days_logged']}/7 days logged)\n"
            if n["low_cal_days"]:
                msg += f"  ⚠️ {n['low_cal_days']} days under target calories\n"

        # Main lifts
        if summary["main_lifts"]:
            msg += "\n📈 Main Lifts:\n"
            for lift in summary["main_lifts"]:
                status = "🔥" if lift["hit_target"] else "🏋️"
                msg += f"  {status} {lift['name']}: {lift['weight']}kg × {lift['sets']}×{lift['reps']}"
                if lift.get("progression"):
                    msg += f" {lift['progression']}"
                msg += "\n"

        # Cycling
        if c["scheduled"] > 0:
            msg += f"\n🚴 Cycling: {c['completed']}/{c['scheduled']} days\n"

        # Steps
        if summary["steps"] and summary["steps"]["avg"]:
            msg += f"\n👟 Avg steps: {summary['steps']['avg']:,}\n"

        # Skincare
        msg += f"\n🧴 Skincare: AM {s['morning']}/{s['total_days']} | PM {s['night']}/{s['total_days']}\n"

        # Health
        if h["urticaria_days"] or h["breakout_days"]:
            msg += "\n🏥 Health:\n"
            if h["urticaria_days"]:
                msg += f"  Urticaria: {h['urticaria_days']} days\n"
            if h["breakout_days"]:
                msg += f"  Breakouts: {h['breakout_days']} days\n"

        return msg

    except Exception as e:
        logger.error(f"Weekly fitness summary error: {e}")
        return f"⚠️ Error generating weekly summary: {e}"


def process_block_summary(action_data: dict) -> str:
    """Generate training block summary."""
    try:
        block_id = action_data.get("block_id")
        summary = generate_block_summary(block_id)

        if "error" in summary:
            return f"⚠️ {summary['error']}"

        t = summary["training"]
        w = summary["weight"]
        n = summary["nutrition"]
        sk = summary["skincare"]

        msg = f"📊 BLOCK SUMMARY — {summary['block']} ({summary['phase'].upper()})\n"
        msg += f"📅 {summary['dates']}\n\n"

        msg += f"🏋️ Training: {t['total_sessions']}/{t['target_sessions']} sessions ({t['adherence_pct']}%)\n"

        if w["start"] and w["end"]:
            change = f"+{w['change']}" if w["change"] and w["change"] > 0 else str(w["change"])
            msg += f"⚖️ Weight: {w['start']}kg → {w['end']}kg ({change}kg)"
            if w["target"]:
                msg += f" [target: {w['target']}kg]"
            msg += "\n"

        if n["avg_calories"]:
            msg += f"🍽️ Avg nutrition: {n['avg_calories']} cal / {n['avg_protein']}g protein"
            if n["target_calories"]:
                cal_diff = n["avg_calories"] - n["target_calories"]
                msg += f" [target: {n['target_calories']}cal, {'+' if cal_diff > 0 else ''}{cal_diff}]"
            msg += f" ({n['days_logged']} days logged)\n"

        if summary["strength"]:
            msg += "\n💪 Strength Progress:\n"
            for key, data in summary["strength"].items():
                arrow = "📈" if data["gain"] > 0 else "➡️"
                msg += f"  {arrow} {data['name']}: {data['start_weight']}kg → {data['end_weight']}kg (+{data['gain']}kg)\n"

        msg += f"\n🧴 Skincare: AM {sk['morning_pct']}% | PM {sk['night_pct']}%\n"
        msg += "\n📸 Remember to take progress photos!"

        return msg

    except Exception as e:
        logger.error(f"Block summary error: {e}")
        return f"⚠️ Error generating block summary: {e}"


def process_create_block(action_data: dict) -> str:
    """Create a new training block and generate all workouts for it."""
    try:
        block = create_training_block(
            name=action_data["name"],
            start_date=action_data["start_date"],
            end_date=action_data["end_date"],
            phase=action_data["phase"],
            calorie_target=action_data.get("calorie_target"),
            protein_target=action_data.get("protein_target"),
            weight_start=action_data.get("weight_start"),
            weight_target=action_data.get("weight_target"),
            cycling_days=action_data.get("cycling_days"),
            notes=action_data.get("notes"),
        )

        msg = f"🏗️ Training block created: {block['name']}\n"
        msg += f"  Phase: {block['phase']} | {block['start_date']} → {block['end_date']}\n"
        if block.get("calorie_target"):
            msg += f"  Targets: {block['calorie_target']} cal / {block.get('protein_target', '?')}g protein\n"
        if block.get("weight_start"):
            msg += f"  Weight: {block['weight_start']}kg → {block.get('weight_target', '?')}kg\n"

        # Auto-generate all workouts for the block
        workout_result = generate_block_workouts(
            block_id=block["id"],
            start_date=action_data["start_date"],
            end_date=action_data["end_date"],
        )

        msg += f"\n📅 Generated {workout_result['sessions_created']} training sessions:\n"
        by_week = {}
        for s in workout_result["sessions"]:
            from datetime import datetime as dt
            d = dt.strptime(s["date"], "%Y-%m-%d")
            week_num = (d - dt.strptime(action_data["start_date"], "%Y-%m-%d")).days // 7 + 1
            if week_num not in by_week:
                by_week[week_num] = []
            day_name = d.strftime("%a %b %d")
            by_week[week_num].append(f"    {day_name}: {s['session_type']} ({s['exercises']} exercises)")

        for week, sessions in sorted(by_week.items()):
            msg += f"  Week {week}:\n"
            msg += "\n".join(sessions) + "\n"

        return msg

    except Exception as e:
        logger.error(f"Create block error: {e}")
        return f"⚠️ Error creating block: {e}"


def process_plan_next_block(action_data: dict) -> str:
    """Auto-plan next month's block using the bulk/cut timeline."""
    try:
        year = action_data["year"]
        month = action_data["month"]
        weight_start = action_data.get("weight_start")

        plan = plan_next_block(year, month, weight_start)

        # Create the block
        block = create_training_block(
            name=plan["name"],
            start_date=plan["start_date"],
            end_date=plan["end_date"],
            phase=plan["phase"],
            calorie_target=plan["calorie_target"],
            protein_target=plan["protein_target"],
            weight_start=weight_start,
        )

        # Generate workouts
        workout_result = generate_block_workouts(
            block_id=block["id"],
            start_date=plan["start_date"],
            end_date=plan["end_date"],
        )

        phase_emoji = {"bulk": "📈", "mini_cut": "✂️", "final_cut": "🔪"}.get(plan["phase"], "📋")

        msg = f"{phase_emoji} {plan['name']} block planned!\n"
        msg += f"  Phase: {plan['phase'].upper()}\n"
        msg += f"  Dates: {plan['start_date']} → {plan['end_date']}\n"
        msg += f"  Nutrition: {plan['calorie_target']} cal / {plan['protein_target']}g protein\n"
        if weight_start:
            msg += f"  Starting weight: {weight_start}kg\n"
        msg += f"\n📅 {workout_result['sessions_created']} sessions generated:\n"

        by_week = {}
        for s in workout_result["sessions"]:
            from datetime import datetime as dt
            d = dt.strptime(s["date"], "%Y-%m-%d")
            week_num = (d - dt.strptime(plan["start_date"], "%Y-%m-%d")).days // 7 + 1
            if week_num not in by_week:
                by_week[week_num] = []
            day_name = d.strftime("%a %b %d")
            by_week[week_num].append(f"    {day_name}: {s['session_type']}")

        for week, sessions in sorted(by_week.items()):
            msg += f"  Week {week}:\n"
            msg += "\n".join(sessions) + "\n"

        return msg

    except Exception as e:
        logger.error(f"Plan next block error: {e}")
        return f"⚠️ Error planning block: {e}"


def process_progress_photos(action_data: dict) -> str:
    """Log that progress photos were taken."""
    try:
        date = action_data.get("date", datetime.now().strftime("%Y-%m-%d"))
        notes = action_data.get("notes")
        log_progress_photos(date=date, notes=notes)
        return f"📸 Progress photos logged for {date}."
    except Exception as e:
        logger.error(f"Progress photos error: {e}")
        return f"⚠️ Error logging photos: {e}"


def process_add_fitness_goal(action_data: dict) -> str:
    """Add a fitness goal."""
    try:
        goal = add_fitness_goal(
            category=action_data["category"],
            goal_text=action_data["goal_text"],
            target_value=action_data.get("target_value"),
            target_date=action_data.get("target_date"),
            notes=action_data.get("notes"),
        )
        msg = f"🎯 Fitness goal added: {goal['goal_text']}"
        if goal.get("target_value"):
            msg += f" → {goal['target_value']}"
        if goal.get("target_date"):
            msg += f" (by {goal['target_date']})"
        return msg
    except Exception as e:
        logger.error(f"Add fitness goal error: {e}")
        return f"⚠️ Error adding goal: {e}"


def process_achieve_fitness_goal(action_data: dict) -> str:
    """Mark a fitness goal as achieved."""
    try:
        success = achieve_fitness_goal(action_data["goal_fragment"])
        if success:
            return f"🏆 Fitness goal achieved: {action_data['goal_fragment']}"
        return f"⚠️ No active goal matching '{action_data['goal_fragment']}'"
    except Exception as e:
        logger.error(f"Achieve fitness goal error: {e}")
        return f"⚠️ Error: {e}"


def process_revise_fitness_goal(action_data: dict) -> str:
    """Revise a fitness goal."""
    try:
        success = revise_fitness_goal(
            goal_fragment=action_data["goal_fragment"],
            new_text=action_data.get("new_text"),
            new_target=action_data.get("new_target"),
        )
        if success:
            return f"📝 Fitness goal revised: {action_data.get('new_text', action_data['goal_fragment'])}"
        return f"⚠️ No active goal matching '{action_data['goal_fragment']}'"
    except Exception as e:
        logger.error(f"Revise fitness goal error: {e}")
        return f"⚠️ Error: {e}"