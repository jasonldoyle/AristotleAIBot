# Actions Reference

All 36 actions Plato can take, grouped by domain.

## Projects (7 actions)

### 1. `log` - Log work on a project
```json
{"action": "log", "project_slug": "...", "summary": "...", "duration_mins": null, "blockers": null, "tags": [], "mood": null}
```
Tags: coding, marketing, research, design, admin, learning, outreach. Moods: energised, neutral, drained, frustrated, flow.

### 2. `create_project` - Create a new project
```json
{"action": "create_project", "name": "...", "slug": "...", "intent": "..."}
```

### 3. `add_soul` - Add soul doc entry
```json
{"action": "add_soul", "content": "...", "category": "goal_lifetime|goal_5yr|goal_2yr|goal_1yr|philosophy|rule|anti_pattern", "trigger": "..."}
```

### 4. `add_goal` - Set a project goal
```json
{"action": "add_goal", "project_slug": "...", "timeframe": "weekly|monthly|quarterly|milestone", "goal_text": "...", "target_date": null}
```

### 5. `achieve_goal` - Mark a goal achieved
```json
{"action": "achieve_goal", "project_slug": "...", "goal_fragment": "..."}
```

### 6. `update_project` - Update project details
```json
{"action": "update_project", "slug": "...", "updates": {"target_date": null, "estimated_weekly_hours": null, "stick_twist_criteria": null, "alignment_rationale": null}}
```

### 7. `add_pattern` - Log a recurring behaviour
```json
{"action": "add_pattern", "pattern_type": "blocker|overestimation|external_constraint|bad_habit|avoidance", "description": "...", "project_slug": null}
```

## Schedule (5 actions)

### 8. `plan_week` - Generate weekly schedule for Google Calendar
```json
{"action": "plan_week", "events": [{"date": "YYYY-MM-DD", "start": "HH:MM", "end": "HH:MM", "title": "...", "description": "...", "category": "cfa|nitrogen|glowbook|plato|leetcode|rest|exercise|personal|citco|audrey"}]}
```

### 9. `audrey_time` - Cancel evening plans for girlfriend time
```json
{"action": "audrey_time", "date": "YYYY-MM-DD", "from_time": "HH:MM"}
```

### 10. `add_event` - Add a one-off calendar event
```json
{"action": "add_event", "date": "YYYY-MM-DD", "start": "HH:MM", "end": "HH:MM", "title": "...", "category": "personal", "description": null}
```

### 11. `check_in` - Record what happened during a planned block
```json
{"action": "check_in", "event_id": "uuid-or-null", "status": "completed|partial|skipped", "actual_summary": "...", "gap_reason": "..."}
```

### 12. `log_fitness` (legacy) - Log exercises
```json
{"action": "log_fitness", "exercises": [...]}
```

## Fitness (15 actions)

### 13. `log_workout` - Log a training session
```json
{"action": "log_workout", "session_type": "Push|Legs|Upper Hypertrophy|Shoulders + Arms", "exercises": [{"exercise": "...", "sets": 4, "reps": 8, "weight_kg": 60, "notes": null}], "feedback": "...", "duration_mins": 65, "date": null}
```

### 14. `daily_log` - Morning check-in / daily data
```json
{"action": "daily_log", "date": null, "weight_kg": 82.1, "steps": null, "sleep_hours": null, "skincare_am": true, "skincare_pm": true, "skincare_notes": null, "cycling_scheduled": false, "cycling_completed": true, "cycling_notes": null, "urticaria_severity": null, "breakout_severity": null, "breakout_location": null, "health_notes": null}
```

### 15. `missed_workout` - Log a missed session
```json
{"action": "missed_workout", "session_type": "Push|Legs|Upper Hypertrophy|Shoulders + Arms", "reason": "...", "date": null}
```

### 16. `confirm_lift` - Confirm weight progression on a main lift
```json
{"action": "confirm_lift", "lift_key": "incline_bench|barbell_row|squat|ohp"}
```

### 17. `weekly_fitness_summary` - Weekly fitness review
```json
{"action": "weekly_fitness_summary", "week_start": "YYYY-MM-DD"}
```

### 18. `block_summary` - 4-week training block review
```json
{"action": "block_summary", "block_id": null}
```

### 19. `create_block` - Create a new training block
```json
{"action": "create_block", "name": "March 2026", "start_date": "2026-03-02", "end_date": "2026-03-29", "phase": "bulk|mini_cut|final_cut", "calorie_target": 3000, "protein_target": 170, "weight_start": 82.0, "weight_target": 83.0, "cycling_days": ["Mon", "Wed", "Fri"], "notes": null}
```

### 20. `plan_next_block` - Auto-plan next month's block
```json
{"action": "plan_next_block", "year": 2026, "month": 3, "weight_start": 82.5}
```

### 21. `todays_workout` - Show today's scheduled session
```json
{"action": "todays_workout", "date": null}
```

### 22. `complete_workout` - Mark session done (exception-based)
```json
{"action": "complete_workout", "date": null, "feedback": "...", "exceptions": [{"exercise": "Lateral Raise", "actual_reps": 6, "notes": "..."}]}
```

### 23. `adjust_exercise` - Change weight for an exercise
```json
{"action": "adjust_exercise", "exercise": "Lateral Raise", "new_weight": 8.0, "reason": "..."}
```

### 24. `progress_photos` - Log that photos were taken
```json
{"action": "progress_photos", "date": null, "notes": "Front, side, back"}
```

### 25. `add_fitness_goal` - Add a fitness goal
```json
{"action": "add_fitness_goal", "category": "body_composition|strength|aesthetic|habit|timeline", "goal_text": "...", "target_value": "...", "target_date": "...", "notes": null}
```

### 26. `achieve_fitness_goal` - Mark a fitness goal achieved
```json
{"action": "achieve_fitness_goal", "goal_fragment": "..."}
```

### 27. `revise_fitness_goal` - Update a fitness goal
```json
{"action": "revise_fitness_goal", "goal_fragment": "...", "new_text": "...", "new_target": "..."}
```

## Finance (2 actions)

### 28. `finance_review` - Spending/savings summary
```json
{"action": "finance_review", "year": 2026, "month": 2}
```

### 29. `set_budget` - Monthly spending limit
```json
{"action": "set_budget", "category": "takeaway", "monthly_limit": 100.00}
```

## Admin (10 actions)

### 30. `add_task` - One-off task
```json
{"action": "add_task", "title": "...", "due_date": "2026-02-14", "due_time": null, "category": "personal|shopping|health|admin|social", "priority": "low|normal|high|urgent", "notes": null}
```

### 31. `complete_task` - Mark task done
```json
{"action": "complete_task", "task_fragment": "..."}
```

### 32. `skip_task` - Skip a task
```json
{"action": "skip_task", "task_fragment": "...", "reason": "..."}
```

### 33. `delete_task` - Remove a task
```json
{"action": "delete_task", "task_fragment": "..."}
```

### 34. `add_recurring` - Recurring task
```json
{"action": "add_recurring", "title": "Laundry", "recurring": "weekly|monthly", "recurring_day": "thursday", "category": "personal"}
```

### 35. `complete_recurring` - Complete this occurrence
```json
{"action": "complete_recurring", "task_fragment": "laundry"}
```

### 36. `delete_recurring` - Remove recurring task permanently
```json
{"action": "delete_recurring", "task_fragment": "laundry"}
```

### 37. `add_date` - Important date (birthday, anniversary)
```json
{"action": "add_date", "title": "Mam's birthday", "month": 3, "day": 15, "year": 1970, "category": "birthday|anniversary|deadline|other", "reminder_days": 7, "notes": null}
```

### 38. `delete_date` - Remove an important date
```json
{"action": "delete_date", "title_fragment": "Mam's birthday"}
```

### 39. `show_tasks` - Display tasks
```json
{"action": "show_tasks", "scope": "today|upcoming|all", "days": 7}
```

## Ideas (2 actions)

### 40. `park_idea` - Park a new idea (14-day cooling period)
```json
{"action": "park_idea", "idea": "...", "context": "Why it came up"}
```

### 41. `resolve_idea` - Approve or reject after cooling
```json
{"action": "resolve_idea", "idea_fragment": "...", "status": "approved|rejected", "notes": "Why"}
```
