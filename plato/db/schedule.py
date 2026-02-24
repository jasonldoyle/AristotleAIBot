import json
from datetime import datetime, timezone

from plato.config import SessionLocal
from plato.models import ScheduleEvent, PendingPlan


def save_pending_plan(week_start: str, events: list) -> str:
    """Save a pending weekly plan. Rejects any existing pending plan for same week."""
    with SessionLocal() as session:
        existing = (
            session.query(PendingPlan)
            .filter_by(week_start=week_start, status="pending")
            .first()
        )
        if existing:
            existing.status = "rejected"
            existing.resolved_at = datetime.now(timezone.utc)

        plan = PendingPlan(
            week_start=week_start,
            events_json=json.dumps(events),
            status="pending",
        )
        session.add(plan)
        session.commit()
        return str(plan.id)


def get_pending_plan() -> dict | None:
    """Get the most recent pending plan."""
    with SessionLocal() as session:
        plan = (
            session.query(PendingPlan)
            .filter_by(status="pending")
            .order_by(PendingPlan.created_at.desc())
            .first()
        )
        if not plan:
            return None
        return {
            "id": str(plan.id),
            "week_start": plan.week_start,
            "events": json.loads(plan.events_json),
            "status": plan.status,
            "created_at": plan.created_at.isoformat() if plan.created_at else None,
        }


def approve_pending_plan(plan_id: str) -> list[dict]:
    """Mark plan as approved, create ScheduleEvent rows, return events for calendar."""
    with SessionLocal() as session:
        plan = session.query(PendingPlan).filter_by(id=plan_id).first()
        if not plan:
            return []

        plan.status = "approved"
        plan.resolved_at = datetime.now(timezone.utc)

        events = json.loads(plan.events_json)
        for ev in events:
            session.add(ScheduleEvent(
                date=ev["date"],
                start_time=ev["start"],
                end_time=ev["end"],
                title=ev["title"],
                category=ev.get("category"),
                status="scheduled",
                week_start=plan.week_start,
            ))

        session.commit()
        return events


def reject_pending_plan(plan_id: str) -> bool:
    """Reject a pending plan."""
    with SessionLocal() as session:
        plan = session.query(PendingPlan).filter_by(id=plan_id).first()
        if not plan:
            return False
        plan.status = "rejected"
        plan.resolved_at = datetime.now(timezone.utc)
        session.commit()
        return True


def save_schedule_event(date: str, start: str, end: str, title: str,
                        category: str = None, week_start: str = None) -> str:
    """Save a single schedule event. Returns event ID."""
    with SessionLocal() as session:
        event = ScheduleEvent(
            date=date,
            start_time=start,
            end_time=end,
            title=title,
            category=category,
            status="scheduled",
            week_start=week_start,
        )
        session.add(event)
        session.commit()
        return str(event.id)


def cancel_schedule_event(date: str, title_keyword: str) -> str | None:
    """Cancel a specific scheduled event by date + title substring. Returns title if found."""
    with SessionLocal() as session:
        event = (
            session.query(ScheduleEvent)
            .filter(
                ScheduleEvent.date == date,
                ScheduleEvent.status == "scheduled",
                ScheduleEvent.title.ilike(f"%{title_keyword}%"),
            )
            .first()
        )
        if not event:
            return None
        event.status = "cancelled"
        title = event.title
        session.commit()
        return title


def update_schedule_event(date: str, title_keyword: str, new_date: str = None,
                          new_start: str = None, new_end: str = None,
                          new_title: str = None) -> dict | None:
    """Update a specific scheduled event. Returns old event dict if found."""
    with SessionLocal() as session:
        event = (
            session.query(ScheduleEvent)
            .filter(
                ScheduleEvent.date == date,
                ScheduleEvent.status == "scheduled",
                ScheduleEvent.title.ilike(f"%{title_keyword}%"),
            )
            .first()
        )
        if not event:
            return None
        old = {
            "date": event.date, "start_time": event.start_time,
            "end_time": event.end_time, "title": event.title,
            "category": event.category,
        }
        if new_date:
            event.date = new_date
        if new_start:
            event.start_time = new_start
        if new_end:
            event.end_time = new_end
        if new_title:
            event.title = new_title
        session.commit()
        return old


def report_deviation(date: str, title_keyword: str, reason: str) -> bool:
    """Mark an event as deviated by matching date + title substring."""
    with SessionLocal() as session:
        events = (
            session.query(ScheduleEvent)
            .filter(
                ScheduleEvent.date == date,
                ScheduleEvent.status == "scheduled",
                ScheduleEvent.title.ilike(f"%{title_keyword}%"),
            )
            .all()
        )
        if not events:
            return False
        for ev in events:
            ev.status = "deviated"
            ev.deviation_reason = reason
        session.commit()
        return True


def cancel_evening_schedule_events(date: str, from_time: str = "18:00") -> int:
    """Cancel DB schedule events for evening of a given date."""
    with SessionLocal() as session:
        events = (
            session.query(ScheduleEvent)
            .filter(
                ScheduleEvent.date == date,
                ScheduleEvent.start_time >= from_time,
                ScheduleEvent.status == "scheduled",
            )
            .all()
        )
        count = 0
        for ev in events:
            ev.status = "cancelled"
            count += 1
        session.commit()
        return count


def get_schedule_for_date(date: str) -> list[dict]:
    """Get today's scheduled events."""
    with SessionLocal() as session:
        rows = (
            session.query(ScheduleEvent)
            .filter(ScheduleEvent.date == date, ScheduleEvent.status == "scheduled")
            .order_by(ScheduleEvent.start_time)
            .all()
        )
        return [
            {
                "id": str(r.id),
                "date": r.date,
                "start_time": r.start_time,
                "end_time": r.end_time,
                "title": r.title,
                "category": r.category,
                "status": r.status,
            }
            for r in rows
        ]


def get_schedule_for_week(week_start: str) -> list[dict]:
    """Get all schedule events for a week (all statuses)."""
    with SessionLocal() as session:
        rows = (
            session.query(ScheduleEvent)
            .filter(ScheduleEvent.week_start == week_start)
            .order_by(ScheduleEvent.date, ScheduleEvent.start_time)
            .all()
        )
        return [
            {
                "id": str(r.id),
                "date": r.date,
                "start_time": r.start_time,
                "end_time": r.end_time,
                "title": r.title,
                "category": r.category,
                "status": r.status,
                "deviation_reason": r.deviation_reason,
            }
            for r in rows
        ]


def format_todays_schedule(events: list[dict]) -> str:
    """Format today's schedule for system prompt injection."""
    if not events:
        return "No scheduled events today."

    lines = []
    for ev in events:
        lines.append(f"- {ev['start_time']}-{ev['end_time']}: {ev['title']} [{ev.get('category', '')}]")
    return "\n".join(lines)
