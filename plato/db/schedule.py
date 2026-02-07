import json
from datetime import datetime, timedelta
from plato.config import supabase


# ============== SCHEDULE EVENTS ==============

def store_schedule_events(events: list[dict]) -> int:
    """Store planned events in schedule_events table for adherence tracking."""
    count = 0
    for event in events:
        entry = {
            "date": event["date"],
            "start_time": event["start"],
            "end_time": event["end"],
            "title": event["title"],
            "category": event.get("category", "personal"),
            "description": event.get("description"),
            "status": "planned"
        }
        supabase.table("schedule_events").insert(entry).execute()
        count += 1
    return count


def get_planned_events_for_date(date_str: str) -> list[dict]:
    """Get planned schedule events for a specific date."""
    result = supabase.table("schedule_events").select("*").eq("date", date_str).order("start_time").execute()
    return result.data


def update_schedule_event(event_id: str, status: str,
                          actual_summary: str = None,
                          gap_reason: str = None) -> bool:
    """Update a schedule event's status and outcome."""
    updates = {"status": status, "updated_at": datetime.now().isoformat()}
    if actual_summary:
        updates["actual_summary"] = actual_summary
    if gap_reason:
        updates["gap_reason"] = gap_reason

    supabase.table("schedule_events").update(updates).eq("id", event_id).execute()
    return True


def mark_evening_audrey(date_str: str, from_time: str = "18:00") -> list[dict]:
    """Mark evening schedule events as audrey_time. Returns affected events."""
    events = supabase.table("schedule_events").select("*").eq("date", date_str).eq("status", "planned").gte("start_time", from_time).execute()

    affected = []
    for event in events.data:
        supabase.table("schedule_events").update({
            "status": "audrey_time",
            "updated_at": datetime.now().isoformat()
        }).eq("id", event["id"]).execute()
        affected.append(event)

    return affected


def get_weekly_adherence(week_start_str: str) -> dict:
    """Calculate schedule adherence stats for a week."""
    week_end = (datetime.strptime(week_start_str, "%Y-%m-%d") + timedelta(days=7)).strftime("%Y-%m-%d")

    result = supabase.table("schedule_events").select("*").gte("date", week_start_str).lt("date", week_end).execute()

    stats = {
        "total": len(result.data),
        "completed": 0,
        "partial": 0,
        "skipped": 0,
        "audrey_time": 0,
        "rescheduled": 0,
        "planned": 0,
        "by_category": {}
    }

    for event in result.data:
        status = event["status"]
        stats[status] = stats.get(status, 0) + 1

        cat = event["category"]
        if cat not in stats["by_category"]:
            stats["by_category"][cat] = {"completed": 0, "total": 0}
        stats["by_category"][cat]["total"] += 1
        if status == "completed":
            stats["by_category"][cat]["completed"] += 1

    if stats["total"] > 0:
        stats["adherence_pct"] = round((stats["completed"] + stats["partial"] * 0.5) / stats["total"] * 100, 1)
    else:
        stats["adherence_pct"] = 0

    return stats


# ============== PENDING PLANS ==============

def store_pending_plan(events: list[dict]) -> None:
    """Store a pending weekly plan for approval."""
    supabase.table("pending_plan").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    supabase.table("pending_plan").insert({"events": json.dumps(events)}).execute()


def get_pending_plan() -> list[dict] | None:
    """Retrieve the pending plan if one exists."""
    result = supabase.table("pending_plan").select("*").order("created_at", desc=True).limit(1).execute()
    if result.data:
        return json.loads(result.data[0]["events"])
    return None


def clear_pending_plan() -> None:
    """Clear the pending plan after approval or rejection."""
    supabase.table("pending_plan").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()