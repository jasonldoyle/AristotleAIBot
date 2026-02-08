from plato.db.core import get_recent_conversations, save_conversation, clear_conversations
from plato.db.projects import (
    get_active_projects, get_unresolved_patterns, get_project_by_slug,
    log_work, create_project, add_project_goal, mark_goal_achieved,
    update_project, add_pattern
)
from plato.db.soul_doc import get_soul_doc, add_soul_doc_entry
from plato.db.fitness import (
    # Legacy compat
    log_fitness_exercises, get_recent_fitness,
    # Daily logs
    log_daily, get_daily_log, get_daily_logs_range, get_weight_history,
    # Training sessions
    log_training_session, log_missed_session, get_training_sessions_range,
    get_recent_training,
    # Main lifts
    get_lift_history, get_all_lift_latest, confirm_progression,
    MAIN_LIFTS, LIFT_ALIASES, SESSION_TYPES,
    # Nutrition
    parse_mfp_diary, import_nutrition, get_nutrition_range, get_recent_nutrition,
    # Blocks
    create_training_block, get_current_block,
    # Summaries
    generate_weekly_summary, generate_block_summary,
    # Progress photos
    log_progress_photos,
)
from plato.db.schedule import (
    store_schedule_events, get_planned_events_for_date,
    update_schedule_event, mark_evening_audrey, get_weekly_adherence,
    store_pending_plan, get_pending_plan, clear_pending_plan
)
from plato.db.ideas import park_idea, get_parked_ideas, resolve_idea
from plato.db.finance import (
    parse_revolut_csv, parse_aib_csv, import_transactions,
    get_transactions_for_month, get_spending_by_category,
    get_monthly_summary, get_budget_limits, set_budget_limit,
    check_budget_alerts, update_transaction_category
)

__all__ = [
    "get_recent_conversations", "save_conversation", "clear_conversations",
    "get_active_projects", "get_unresolved_patterns", "get_project_by_slug",
    "log_work", "create_project", "add_project_goal", "mark_goal_achieved",
    "update_project", "add_pattern",
    "get_soul_doc", "add_soul_doc_entry",
    "log_fitness_exercises", "get_recent_fitness",
    "log_daily", "get_daily_log", "get_daily_logs_range", "get_weight_history",
    "log_training_session", "log_missed_session", "get_training_sessions_range",
    "get_recent_training",
    "get_lift_history", "get_all_lift_latest", "confirm_progression",
    "MAIN_LIFTS", "LIFT_ALIASES", "SESSION_TYPES",
    "parse_mfp_diary", "import_nutrition", "get_nutrition_range", "get_recent_nutrition",
    "create_training_block", "get_current_block",
    "generate_weekly_summary", "generate_block_summary",
    "log_progress_photos",
    "store_schedule_events", "get_planned_events_for_date",
    "update_schedule_event", "mark_evening_audrey", "get_weekly_adherence",
    "store_pending_plan", "get_pending_plan", "clear_pending_plan",
    "park_idea", "get_parked_ideas", "resolve_idea",
    "parse_revolut_csv", "parse_aib_csv", "import_transactions",
    "get_transactions_for_month", "get_spending_by_category",
    "get_monthly_summary", "get_budget_limits", "set_budget_limit",
    "check_budget_alerts", "update_transaction_category",
]