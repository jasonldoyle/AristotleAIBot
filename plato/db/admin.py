"""
Admin task management — one-off tasks, recurring tasks, and important dates.
"""

from datetime import datetime, timedelta
from plato.config import supabase, logger

DAY_NAMES = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}
DAY_LOOKUP = {v.lower(): k for k, v in DAY_NAMES.items()}
DAY_LOOKUP.update({
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
})


# ============== ONE-OFF TASKS ==============

def add_task(
    title: str, due_date: str = None, due_time: str = None,
    category: str = "personal", priority: str = "normal", notes: str = None
) -> dict:
    """Add a one-off task."""
    result = supabase.table("admin_tasks").insert({
        "title": title, "due_date": due_date, "due_time": due_time,
        "category": category, "priority": priority, "notes": notes,
    }).execute()
    return result.data[0]


def complete_task(task_fragment: str) -> bool:
    """Mark a task as done by partial title match."""
    tasks = get_pending_tasks()
    for t in tasks:
        if task_fragment.lower() in t["title"].lower():
            supabase.table("admin_tasks").update({
                "status": "done",
                "completed_at": datetime.now().isoformat(),
            }).eq("id", t["id"]).execute()
            return True
    return False


def skip_task(task_fragment: str, reason: str = None) -> bool:
    """Skip a task."""
    tasks = get_pending_tasks()
    for t in tasks:
        if task_fragment.lower() in t["title"].lower():
            supabase.table("admin_tasks").update({
                "status": "skipped",
                "notes": reason or t.get("notes"),
            }).eq("id", t["id"]).execute()
            return True
    return False


def delete_task(task_fragment: str) -> bool:
    """Delete a task entirely."""
    tasks = supabase.table("admin_tasks").select("*").neq(
        "status", "done"
    ).execute()
    for t in tasks.data:
        if task_fragment.lower() in t["title"].lower():
            supabase.table("admin_tasks").delete().eq("id", t["id"]).execute()
            return True
    return False


# ============== RECURRING TASKS ==============

def add_recurring_task(
    title: str, recurring: str, recurring_day: int = None,
    recurring_month: int = None, category: str = "personal",
    priority: str = "normal", notes: str = None
) -> dict:
    """Add a recurring task. recurring: weekly, monthly, yearly."""
    result = supabase.table("admin_tasks").insert({
        "title": title, "recurring": recurring,
        "recurring_day": recurring_day, "recurring_month": recurring_month,
        "category": category, "priority": priority, "notes": notes,
        "status": "pending",
    }).execute()
    return result.data[0]


def complete_recurring(task_fragment: str) -> bool:
    """Mark a recurring task as done for this occurrence.
    Resets it to pending (it'll show up again next cycle)."""
    tasks = get_recurring_tasks()
    for t in tasks:
        if task_fragment.lower() in t["title"].lower():
            supabase.table("admin_tasks").update({
                "completed_at": datetime.now().isoformat(),
            }).eq("id", t["id"]).execute()
            return True
    return False


def delete_recurring(task_fragment: str) -> bool:
    """Delete a recurring task permanently."""
    tasks = get_recurring_tasks()
    for t in tasks:
        if task_fragment.lower() in t["title"].lower():
            supabase.table("admin_tasks").delete().eq("id", t["id"]).execute()
            return True
    return False


# ============== IMPORTANT DATES ==============

def add_important_date(
    title: str, date_month: int, date_day: int, year: int = None,
    category: str = "birthday", reminder_days: int = 7, notes: str = None
) -> dict:
    """Add a birthday, anniversary, or other important date."""
    result = supabase.table("important_dates").insert({
        "title": title, "date_month": date_month, "date_day": date_day,
        "year": year, "category": category, "reminder_days": reminder_days,
        "notes": notes,
    }).execute()
    return result.data[0]


def delete_important_date(title_fragment: str) -> bool:
    """Delete an important date."""
    dates = get_all_important_dates()
    for d in dates:
        if title_fragment.lower() in d["title"].lower():
            supabase.table("important_dates").delete().eq("id", d["id"]).execute()
            return True
    return False


def get_all_important_dates() -> list[dict]:
    """Get all important dates."""
    result = supabase.table("important_dates").select("*").order("date_month").order("date_day").execute()
    return result.data


# ============== QUERIES ==============

def get_pending_tasks() -> list[dict]:
    """Get all pending one-off tasks (not recurring)."""
    result = supabase.table("admin_tasks").select("*").eq(
        "status", "pending"
    ).is_("recurring", "null").order("due_date").execute()
    return result.data


def get_recurring_tasks() -> list[dict]:
    """Get all recurring tasks."""
    result = supabase.table("admin_tasks").select("*").not_.is_(
        "recurring", "null"
    ).execute()
    return result.data


def get_tasks_for_date(date: str = None) -> list[dict]:
    """Get all tasks relevant to a specific date — due tasks + recurring that match."""
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    date_obj = datetime.strptime(date, "%Y-%m-%d")
    weekday = date_obj.weekday()
    day_of_month = date_obj.day

    tasks = []

    # One-off tasks due on this date
    due_tasks = supabase.table("admin_tasks").select("*").eq(
        "due_date", date
    ).eq("status", "pending").is_("recurring", "null").execute()
    tasks.extend(due_tasks.data)

    # Overdue tasks (due before today, still pending)
    overdue = supabase.table("admin_tasks").select("*").lt(
        "due_date", date
    ).eq("status", "pending").is_("recurring", "null").execute()
    for t in overdue.data:
        t["_overdue"] = True
    tasks.extend(overdue.data)

    # Weekly recurring tasks for this weekday
    weekly = supabase.table("admin_tasks").select("*").eq(
        "recurring", "weekly"
    ).eq("recurring_day", weekday).execute()
    # Only show if not already completed today
    for t in weekly.data:
        if t.get("completed_at"):
            completed_date = t["completed_at"][:10]
            if completed_date == date:
                continue
        t["_recurring_due"] = True
        tasks.append(t)

    # Monthly recurring tasks for this day of month
    monthly = supabase.table("admin_tasks").select("*").eq(
        "recurring", "monthly"
    ).eq("recurring_day", day_of_month).execute()
    for t in monthly.data:
        if t.get("completed_at"):
            completed_date = t["completed_at"][:10]
            if completed_date == date:
                continue
        t["_recurring_due"] = True
        tasks.append(t)

    return tasks


def get_overdue_tasks() -> list[dict]:
    """Get all overdue one-off tasks."""
    today = datetime.now().strftime("%Y-%m-%d")
    result = supabase.table("admin_tasks").select("*").lt(
        "due_date", today
    ).eq("status", "pending").is_("recurring", "null").execute()
    return result.data


def get_upcoming_tasks(days: int = 7) -> list[dict]:
    """Get tasks due in the next N days."""
    today = datetime.now().strftime("%Y-%m-%d")
    end = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    result = supabase.table("admin_tasks").select("*").gte(
        "due_date", today
    ).lte("due_date", end).eq("status", "pending").is_(
        "recurring", "null"
    ).order("due_date").execute()
    return result.data


def get_upcoming_dates(days: int = 30) -> list[dict]:
    """Get important dates coming up in the next N days."""
    today = datetime.now()
    upcoming = []

    dates = get_all_important_dates()
    for d in dates:
        # Build this year's date
        try:
            this_year = datetime(today.year, d["date_month"], d["date_day"])
        except ValueError:
            continue

        # If already passed this year, check next year
        if this_year.date() < today.date():
            try:
                this_year = datetime(today.year + 1, d["date_month"], d["date_day"])
            except ValueError:
                continue

        days_until = (this_year.date() - today.date()).days
        if days_until <= days:
            d["_next_date"] = this_year.strftime("%Y-%m-%d")
            d["_days_until"] = days_until
            if d.get("year"):
                d["_age"] = this_year.year - d["year"]
            upcoming.append(d)

    upcoming.sort(key=lambda x: x["_days_until"])
    return upcoming


def mark_overdue_tasks() -> int:
    """Mark past-due tasks as overdue. Returns count updated."""
    today = datetime.now().strftime("%Y-%m-%d")
    result = supabase.table("admin_tasks").update({
        "status": "overdue"
    }).lt("due_date", today).eq("status", "pending").is_(
        "recurring", "null"
    ).execute()
    return len(result.data)