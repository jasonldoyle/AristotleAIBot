from datetime import datetime, timedelta

from plato.config import logger
from plato.db import (
    add_soul_entry,
    update_soul_entry,
    get_soul_doc,
    format_soul_doc,
    store_idea,
    park_idea,
    get_ideas,
    format_ideas,
    resolve_idea,
    create_project,
    get_projects,
    get_project_by_slug,
    update_project_status,
    add_project_goal,
    achieve_goal,
    log_work,
    get_project_summary,
    format_projects_summary,
    format_project_detail,
    save_pending_plan,
    get_pending_plan,
    approve_pending_plan,
    cancel_evening_schedule_events,
    cancel_schedule_event,
    update_schedule_event,
    save_schedule_event,
    report_deviation as db_report_deviation,
    # Fitness
    get_or_create_session,
    log_session,
    log_exercises_bulk,
    log_weigh_in,
    get_weight_trend,
    log_nutrition_batch,
    get_nutrition_averages,
    log_sleep,
    get_sleep_average,
    create_modification,
    create_override_block,
    get_current_block,
    format_fitness_detail,
    # Progression engine
    seed_progression,
    get_day_prescription,
    advance_progression,
    sync_progression_from_actual,
    auto_complete_week,
    TRAINING_SPLIT,
    DAY_WEEKDAY_MAP,
)
from plato.calendar import (
    get_calendar_service,
    clear_plato_events,
    cancel_evening_events,
    cancel_specific_event,
    create_event,
    create_weekly_events,
    get_schedule_prompt,
    COLOR_MAP,
)


def _compute_week_start(week: str = "this") -> str:
    """Return Monday for the requested week. 'this' = current week, 'next' = next week."""
    today = datetime.now()
    weekday = today.weekday()  # 0=Mon
    monday = today - timedelta(days=weekday)
    if week == "next":
        monday += timedelta(days=7)
    return monday.strftime("%Y-%m-%d")


def process_action(action: dict) -> str:
    """Route a JSON action block from Claude and return a status message."""
    action_type = action.get("action")
    try:
        match action_type:
            case "add_soul":
                entry_id = add_soul_entry(action["category"], action["content"])
                return f"Soul doc entry added ({action['category']})."

            case "update_soul":
                entry_id = update_soul_entry(action["category"], action["old_content"], action["content"])
                return f"Soul doc entry updated ({action['category']})."

            case "store_idea":
                idea_id = store_idea(action["idea"], action.get("context"))
                return f"Idea stored."

            case "park_idea":
                found = park_idea(action["idea_id"])
                if found:
                    return "Idea parked. 14-day cooling period started."
                return "Idea not found."

            case "resolve_idea":
                found = resolve_idea(action["idea_id"], action["status"], action.get("notes"))
                if found:
                    return f"Idea {action['status']}."
                return "Idea not found."

            case "query_soul":
                grouped = get_soul_doc()
                return format_soul_doc(grouped)

            case "query_ideas":
                ideas = get_ideas()
                return format_ideas(ideas)

            case "create_project":
                project_id = create_project(action["name"], action["slug"], action.get("intent"))
                return f"Project '{action['name']}' created (slug: {action['slug']})."

            case "log_work":
                project = get_project_by_slug(action["slug"])
                if not project:
                    return f"Project '{action['slug']}' not found."
                log_work(project["id"], action["summary"], action.get("duration_mins"), action.get("mood"))
                return f"Work logged on {project['name']}."

            case "add_goal":
                project = get_project_by_slug(action["slug"])
                if not project:
                    return f"Project '{action['slug']}' not found."
                add_project_goal(project["id"], action["timeframe"], action["goal_text"], action.get("target_date"))
                return f"Goal added to {project['name']} ({action['timeframe']})."

            case "achieve_goal":
                found = achieve_goal(action["goal_id"])
                if found:
                    return "Goal achieved! Well done."
                return "Goal not found."

            case "update_project":
                project = get_project_by_slug(action["slug"])
                if not project:
                    return f"Project '{action['slug']}' not found."
                update_project_status(project["id"], action["status"])
                return f"Project '{project['name']}' status updated to {action['status']}."

            case "query_projects":
                projects = get_projects(status="active")
                return format_projects_summary(projects)

            case "query_project":
                summary = get_project_summary(action["slug"])
                return format_project_detail(summary)

            # --- Schedule actions ---

            case "plan_week":
                events = action["events"]
                week = action.get("week", "this")
                week_start = _compute_week_start(week)

                # Auto-complete unlogged sessions from current week before planning
                current_week_start = _compute_week_start("this")
                auto_results = auto_complete_week(current_week_start)
                auto_completed = [r for r in auto_results if r["status"] == "auto_completed"]

                plan_id = save_pending_plan(week_start, events)

                # Format preview
                lines = []

                # Report auto-completion if it happened
                if auto_completed:
                    day_strs = []
                    for r in auto_completed:
                        day_info = TRAINING_SPLIT.get(r["day_label"], {})
                        day_short = day_info.get("weekday", r["day_label"])[:3]
                        day_strs.append(f"{day_short} {r['date'][-5:]} ✓")
                    lines.append(f"Auto-completed {len(auto_completed)} session(s) from this week ({', '.join(day_strs)}). Progressions advanced.\n")

                lines.append(f"Week of {week_start}:\n")
                current_date = None
                for ev in sorted(events, key=lambda e: (e["date"], e["start"])):
                    if ev["date"] != current_date:
                        current_date = ev["date"]
                        day_name = datetime.strptime(ev["date"], "%Y-%m-%d").strftime("%A %b %d")
                        lines.append(f"\n{day_name}:")
                    lines.append(f"  {ev['start']}-{ev['end']}: {ev['title']} [{ev.get('category', '')}]")

                # Append workout prescriptions for the planned week
                lines.append("\n\n--- Workout Prescriptions ---")
                for day_label_key in ["day1_chest", "day2_back", "day3_legs", "day4_shoulders"]:
                    day_info = TRAINING_SPLIT[day_label_key]
                    prescriptions = get_day_prescription(day_label_key)
                    lines.append(f"\n{day_info['weekday']} ({day_info['label']}):")
                    for p in prescriptions:
                        if p.get("excluded"):
                            lines.append(f"  {p['display']}: {p['sets']}×{p['reps']}")
                        elif p.get("needs_seed"):
                            lines.append(f"  {p['display']}: ⚠ needs seeding ({p['rep_range']})")
                        else:
                            lines.append(f"  {p['display']}: {p['weight_kg']}kg × {p['sets']}×{p['reps']}")

                lines.append(f"\nTotal events: {len(events)}")
                lines.append("Reply 'approve' to push to Google Calendar, or suggest changes.")
                return "\n".join(lines)

            case "approve_plan":
                pending = get_pending_plan()
                if not pending:
                    return "No pending plan to approve."

                events = approve_pending_plan(pending["id"])
                if not events:
                    return "Failed to approve plan."

                try:
                    service = get_calendar_service()
                    week_start_dt = datetime.strptime(pending["week_start"], "%Y-%m-%d")
                    clear_plato_events(service, week_start_dt)
                    count = create_weekly_events(service, events)
                    return f"Plan approved. {count} events pushed to Google Calendar."
                except Exception as e:
                    logger.error(f"Calendar push failed: {e}")
                    return f"Plan approved in DB, but calendar push failed: {e}"

            case "audrey_time":
                date_str = action.get("date", datetime.now().strftime("%Y-%m-%d"))

                # Cancel in DB
                db_count = cancel_evening_schedule_events(date_str)

                # Cancel on Google Calendar
                cancelled_titles = []
                try:
                    service = get_calendar_service()
                    cancelled_titles = cancel_evening_events(service, date_str)
                except Exception as e:
                    logger.error(f"Calendar cancellation failed: {e}")

                if cancelled_titles:
                    return f"Evening cleared for Audrey time. Cancelled: {', '.join(cancelled_titles)}"
                elif db_count > 0:
                    return f"Evening cleared for Audrey time. {db_count} events cancelled."
                else:
                    return "Evening cleared for Audrey time. No scheduled events to cancel."

            case "report_deviation":
                date_str = action.get("date", datetime.now().strftime("%Y-%m-%d"))
                found = db_report_deviation(date_str, action["title"], action["reason"])
                if found:
                    return f"Deviation logged for {date_str}: {action['reason']}"
                return f"Deviation noted for {date_str}: {action['reason']} (no matching scheduled event found)"

            case "add_event":
                date_str = action["date"]
                start = action["start"]
                end = action["end"]
                title = action["title"]
                category = action.get("category", "personal")

                # Save to DB
                save_schedule_event(date_str, start, end, title, category)

                # Push to Google Calendar
                try:
                    service = get_calendar_service()
                    color = COLOR_MAP.get(category)
                    create_event(service, date_str, start, end, title, action.get("description"), color)
                except Exception as e:
                    logger.error(f"Calendar event creation failed: {e}")
                    return f"Event '{title}' saved to DB on {date_str} {start}-{end}, but calendar push failed: {e}"

                return f"Event '{title}' added on {date_str} {start}-{end}."

            case "cancel_event":
                date_str = action["date"]
                title_keyword = action["title"]

                # Cancel in DB
                cancelled_title = cancel_schedule_event(date_str, title_keyword)

                # Cancel on Google Calendar
                try:
                    service = get_calendar_service()
                    cancel_specific_event(service, date_str, title_keyword)
                except Exception as e:
                    logger.error(f"Calendar cancellation failed: {e}")

                if cancelled_title:
                    return f"Cancelled '{cancelled_title}' on {date_str}."
                return f"No scheduled event matching '{title_keyword}' found on {date_str}."

            case "edit_event":
                date_str = action["date"]
                title_keyword = action["title"]
                new_date = action.get("new_date", date_str)
                new_start = action.get("new_start")
                new_end = action.get("new_end")
                new_title = action.get("new_title")

                # Update in DB
                old = update_schedule_event(date_str, title_keyword,
                                            new_date=new_date, new_start=new_start,
                                            new_end=new_end, new_title=new_title)
                if not old:
                    return f"No scheduled event matching '{title_keyword}' found on {date_str}."

                # Update on Google Calendar: cancel old + create new
                try:
                    service = get_calendar_service()
                    cancel_specific_event(service, date_str, title_keyword)
                    color = COLOR_MAP.get(old.get("category", ""))
                    create_event(service, new_date,
                                 new_start or old["start_time"],
                                 new_end or old["end_time"],
                                 new_title or old["title"],
                                 color_id=color)
                except Exception as e:
                    logger.error(f"Calendar edit failed: {e}")
                    return f"Event updated in DB, but calendar sync failed: {e}"

                return f"Event updated: '{old['title']}' on {date_str} -> '{new_title or old['title']}' on {new_date} {new_start or old['start_time']}-{new_end or old['end_time']}."

            # --- Fitness actions ---

            case "log_workout":
                date_str = action.get("date", datetime.now().strftime("%Y-%m-%d"))
                day_label = action["day_label"]
                status = action.get("status", "completed")
                feedback = action.get("feedback")
                lifts = action.get("lifts", [])

                # Create or get session
                ws = get_or_create_session(date_str, day_label)
                # Update status/feedback if session was auto-created as completed
                if status != "completed" or feedback:
                    log_session(date_str, day_label, status=status, feedback=feedback,
                                deviation_notes=action.get("deviation_notes"))

                # Log any lifts and sync progression state
                count = 0
                progression_updates = []
                if lifts:
                    count = log_exercises_bulk(ws["id"], lifts)
                    # Sync progression to match actual reported numbers
                    for lift in lifts:
                        sync_result = sync_progression_from_actual(
                            lift["exercise"], lift["weight_kg"], lift["reps"]
                        )
                        if sync_result and sync_result.get("synced"):
                            progression_updates.append(
                                f"{lift['exercise']}: adjusted to {lift['weight_kg']}kg×{lift['reps']}"
                            )
                    # Advance progression from reported state
                    for lift in lifts:
                        advance_progression(lift["exercise"])

                parts = [f"Workout logged: {day_label} on {date_str} [{status}]"]
                if count:
                    parts.append(f"{count} exercise(s) recorded")
                if progression_updates:
                    parts.append(f"Progression synced: {'; '.join(progression_updates)}")
                if feedback:
                    parts.append(f"Feedback: {feedback}")
                return ". ".join(parts) + "."

            case "missed_workout":
                date_str = action.get("date", datetime.now().strftime("%Y-%m-%d"))
                day_label = action["day_label"]
                reason = action.get("reason", "")
                log_session(date_str, day_label, status="missed", deviation_notes=reason)
                day_info = TRAINING_SPLIT.get(day_label, {})
                label = day_info.get("label", day_label)
                return f"Missed session logged: {label} on {date_str}. {('Reason: ' + reason) if reason else 'No reason given.'}"

            case "log_weight":
                date_str = action.get("date", datetime.now().strftime("%Y-%m-%d"))
                weight_kg = action["weight_kg"]
                log_weigh_in(date_str, weight_kg, action.get("notes"))
                trend = get_weight_trend()
                block = get_current_block()
                parts = [f"Weight logged: {weight_kg}kg on {date_str}"]
                if trend["avg_4wk"]:
                    parts.append(f"4-wk avg: {trend['avg_4wk']}kg")
                if trend["rate_per_week"] is not None:
                    sign = "+" if trend["rate_per_week"] > 0 else ""
                    parts.append(f"rate: {sign}{trend['rate_per_week']}kg/wk")
                if block:
                    parts.append(f"phase: {block['name']}")
                return " | ".join(parts)

            case "log_nutrition":
                days = action.get("days", [])
                if not days:
                    return "No daily entries provided. Paste the weekly MFP export."

                count = log_nutrition_batch(days)

                # Build weekly summary from the batch
                avg_cals = round(sum(d["calories"] for d in days) / len(days))
                avg_protein = round(sum(d["protein_g"] for d in days) / len(days))
                avg_carbs = round(sum(d["carbs_g"] for d in days) / len(days))
                avg_fat = round(sum(d["fat_g"] for d in days) / len(days))
                dates = [d["date"] for d in days]

                block = get_current_block()
                parts = [
                    f"Nutrition logged: {count} days ({dates[0]} to {dates[-1]})",
                    f"Avg: {avg_cals} kcal | {avg_protein}g P | {avg_carbs}g C | {avg_fat}g F",
                ]
                if block and block["calorie_target"]:
                    cal_diff = avg_cals - block["calorie_target"]
                    sign = "+" if cal_diff > 0 else ""
                    parts.append(f"{sign}{cal_diff} vs target {block['calorie_target']}")
                if block and block["protein_target"]:
                    p_diff = avg_protein - block["protein_target"]
                    sign = "+" if p_diff > 0 else ""
                    parts.append(f"protein: {sign}{p_diff} vs {block['protein_target']}g target")
                return " | ".join(parts)

            case "log_sleep":
                date_str = action.get("date", datetime.now().strftime("%Y-%m-%d"))
                hours = action["hours"]
                log_sleep(date_str, hours, action.get("notes"))
                avg = get_sleep_average()
                parts = [f"Sleep logged: {hours}h on {date_str}"]
                if avg["avg"]:
                    parts.append(f"7-day avg: {avg['avg']}h")
                    if avg["below_7"]:
                        parts.append("⚠ below 7h target")
                return " | ".join(parts)

            case "modify_workout":
                mod_id = create_modification(
                    exercise=action["exercise"],
                    modification_type=action["modification_type"],
                    detail=action["detail"],
                    reason=action.get("reason"),
                    valid_from=action.get("valid_from"),
                    valid_until=action.get("valid_until"),
                )
                until_str = action.get("valid_until") or "permanent"
                return f"Workout modification created: {action['exercise']} → {action['detail']} (from {action.get('valid_from', 'today')}, {until_str})."

            case "override_block":
                block_id = create_override_block(
                    name=action["name"],
                    phase=action["phase"],
                    start_date=action["start_date"],
                    calorie_target=action.get("calorie_target"),
                    protein_target=action.get("protein_target"),
                    fat_min=action.get("fat_min"),
                    fat_max=action.get("fat_max"),
                    notes=action.get("notes"),
                )
                return f"Phase override created: {action['name']} ({action['phase']}) starting {action['start_date']}."

            case "seed_progression":
                exercises = action.get("exercises", [])
                if not exercises:
                    return "No exercises provided for seeding."
                results = []
                for entry in exercises:
                    result = seed_progression(
                        exercise=entry["exercise"],
                        weight_kg=entry["weight_kg"],
                        starting_reps=entry.get("starting_reps"),
                    )
                    ex_info = TRAINING_SPLIT
                    # Find display name
                    display = entry["exercise"]
                    for day_data in TRAINING_SPLIT.values():
                        for ex in day_data["exercises"]:
                            if ex["name"] == entry["exercise"]:
                                display = ex["display"]
                                break
                    results.append(f"{display}: {result['weight_kg']}kg × {result['current_reps']} reps [{result['status']}]")
                return f"Seeded {len(results)} exercise(s):\n" + "\n".join(results)

            case "query_fitness":
                return format_fitness_detail()

            case _:
                logger.warning(f"Unknown action type: {action_type}")
                return f"Unknown action: {action_type}"

    except Exception as e:
        logger.error(f"Action '{action_type}' failed: {e}")
        return f"Action failed: {e}"
