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
    get_planned_events_for_date, mark_evening_audrey, park_idea, resolve_idea
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
    """Store plan as pending for approval."""
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
    """Push the pending plan to Google Calendar."""
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
    """Cancel evening events and report what's bumped."""
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
    """Add a one-off event to calendar."""
    try:
        service = get_calendar_service()

        date_str = action_data["date"]
        start = action_data["start"]
        end = action_data["end"]
        title = action_data["title"]
        category = action_data.get("category", "personal")
        description = action_data.get("description")

        create_event(
            service,
            date_str=date_str,
            start_time=start,
            end_time=end,
            title=title,
            description=description,
            color_id=COLOR_MAP.get(category)
        )

        msg = f"📌 Added: {title} on {date_str} {start}-{end}"
        return msg

    except Exception as e:
        logger.error(f"Add event error: {e}")
        return f"⚠️ Error adding event: {e}"


def process_check_in(action_data: dict) -> str:
    """Update schedule event with actual outcome."""
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