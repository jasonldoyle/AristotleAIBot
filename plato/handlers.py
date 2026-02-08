"""
Telegram message and command handlers for Plato bot.
"""

import json
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from plato.config import ALLOWED_USER_ID, anthropic_client, logger
from plato.db import (
    save_conversation, clear_conversations, get_active_projects,
    get_unresolved_patterns, get_planned_events_for_date,
    get_weekly_adherence, get_pending_plan, get_all_lift_latest,
    get_current_block, get_recent_training, MAIN_LIFTS,
)
from plato.prompts import build_system_prompt, build_messages_with_history
from plato.actions import process_action, process_approve_plan, process_import_csv, process_import_mfp
from plato_calendar import get_schedule_prompt


# ============== PLAN WEEK DETECTION ==============

PLAN_TRIGGERS = [
    "plan my week", "plan the week", "schedule my week",
    "what should my week look like", "weekly plan",
    "plan this week", "plan next week"
]


def detect_plan_week(user_message: str) -> str | None:
    """Check if user is asking to plan their week. Returns schedule prompt or None."""
    msg_lower = user_message.lower()

    for trigger in PLAN_TRIGGERS:
        if trigger in msg_lower:
            today = datetime.now()
            if "next week" in msg_lower:
                days_ahead = 7 - today.weekday()
                week_start = today + timedelta(days=days_ahead)
            else:
                week_start = today - timedelta(days=today.weekday())

            week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
            return get_schedule_prompt(week_start)

    return None


# ============== MFP DETECTION ==============

MFP_MARKERS = [
    "Printable Diary for",
    "FOODSCaloriesCarbsFat",
    "EXERCISESCaloriesminutes",
    "MyFitnessPal",
]


def is_mfp_diary(text: str) -> bool:
    """Detect if pasted text is an MFP printable diary."""
    return any(marker in text for marker in MFP_MARKERS)


# ============== MESSAGE HANDLER ==============

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages."""
    user_id = update.effective_user.id

    if user_id != ALLOWED_USER_ID:
        await update.message.reply_text("Plato serves only one master.")
        return

    user_message = update.message.text
    logger.info(f"Received: {user_message[:100]}...")

    # Save user message to history
    save_conversation("user", user_message)

    # Check for plan approval/rejection
    msg_lower = user_message.lower().strip()
    if msg_lower in ["approve", "approved", "looks good", "push it", "send it", "go ahead", "lgtm"]:
        result = process_approve_plan()
        save_conversation("assistant", result)
        await update.message.reply_text(result)
        return

    # Check if this is pasted MFP diary data
    if is_mfp_diary(user_message):
        await update.message.reply_text("🍽️ MFP diary detected, parsing...")
        result = process_import_mfp(user_message)
        save_conversation("user", "[Pasted MFP diary data]")
        save_conversation("assistant", result)
        await update.message.reply_text(result)
        return

    # Check if planning week — add schedule context if so
    schedule_context = detect_plan_week(user_message) or ""

    # If there's a pending plan and user is requesting changes, include it in context
    pending_plan_context = ""
    pending = get_pending_plan()
    if pending and not schedule_context:
        pending_plan_context = f"\n\n## PENDING PLAN (awaiting approval)\nThere is a pending weekly plan with {len(pending)} events. The user may be requesting changes to it. If they request changes, generate a new plan_week action with the modified events.\n"

    system_prompt = build_system_prompt(schedule_context=schedule_context + pending_plan_context)
    messages = build_messages_with_history(user_message)

    # Use higher max_tokens for week planning (lots of JSON events)
    max_tokens = 4096 if (schedule_context or pending_plan_context) else 1024

    response = anthropic_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=max_tokens,
        system=system_prompt,
        messages=messages
    )

    reply = response.content[0].text
    error_msg = None

    # Process JSON action if present
    if "```json" in reply:
        try:
            json_start = reply.index("```json") + 7
            json_end = reply.index("```", json_start)
            json_str = reply[json_start:json_end].strip()
            action_data = json.loads(json_str)

            error_msg = process_action(action_data, user_message)

            # Remove JSON block from reply
            reply = reply[:reply.index("```json")] + reply[json_end + 3:]
            reply = reply.strip()
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse action JSON: {e}")

    # Prepend error/status message if any
    if error_msg:
        reply = f"{error_msg}\n\n{reply}"

    # Save assistant response to history
    save_conversation("assistant", reply)

    await update.message.reply_text(reply)


# ============== COMMAND HANDLERS ==============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    if update.effective_user.id != ALLOWED_USER_ID:
        return
    await update.message.reply_text("Plato is ready. What have you been working on?")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command - quick overview."""
    if update.effective_user.id != ALLOWED_USER_ID:
        return

    projects = get_active_projects()
    patterns = get_unresolved_patterns()

    msg = "📊 Current Status\n\n"
    for p in projects:
        msg += f"• {p['name']}: {len(p.get('recent_logs', []))} recent logs\n"
        if p.get("current_goals"):
            msg += f"  Goals: {len(p['current_goals'])} active\n"

    if patterns:
        msg += f"\n⚠️ {len(patterns)} unresolved patterns"

    # Today's schedule
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        today_events = get_planned_events_for_date(today)
        if today_events:
            msg += "\n\n📅 Today's Schedule:\n"
            for e in today_events:
                status_icon = {"planned": "⬜", "completed": "✅", "partial": "🟡", "skipped": "❌", "audrey_time": "💕"}.get(e["status"], "⬜")
                msg += f"  {status_icon} {e['start_time'][:5]}-{e['end_time'][:5]}: {e['title']}\n"
    except Exception:
        pass

    # Weekly adherence
    try:
        today_dt = datetime.now()
        week_start = (today_dt - timedelta(days=today_dt.weekday())).strftime("%Y-%m-%d")
        stats = get_weekly_adherence(week_start)
        if stats["total"] > 0:
            msg += f"\n📈 This week: {stats['adherence_pct']}% adherence ({stats['completed']}/{stats['total']} blocks)"
            if stats["audrey_time"] > 0:
                msg += f"\n💕 Audrey time: {stats['audrey_time']} blocks"
    except Exception:
        pass

    # Fitness snapshot
    try:
        sessions = get_recent_training(days=7)
        completed = [s for s in sessions if s["completed"]]
        if sessions:
            msg += f"\n\n💪 Training: {len(completed)}/4 sessions this week"

        block = get_current_block()
        if block:
            msg += f"\n🏗️ Block: {block['name']} ({block['phase']})"

        lifts = get_all_lift_latest()
        pending = [k for k, v in lifts.items() if v.get("hit_target") and not v.get("confirmed")]
        if pending:
            names = [MAIN_LIFTS[k]["name"] for k in pending]
            msg += f"\n📈 Pending progressions: {', '.join(names)}"
    except Exception:
        pass

    await update.message.reply_text(msg)


async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /clear command - clear conversation history."""
    if update.effective_user.id != ALLOWED_USER_ID:
        return

    clear_conversations()
    await update.message.reply_text("Conversation history cleared. Fresh start.")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle uploaded documents (CSV for finance, text for MFP)."""
    if update.effective_user.id != ALLOWED_USER_ID:
        return

    document = update.message.document
    filename = document.file_name.lower()

    # Download file
    file = await document.get_file()
    file_bytes = await file.download_as_bytearray()

    try:
        file_content = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        await update.message.reply_text("⚠️ Couldn't read this file. Please upload a CSV or text file.")
        return

    # Detect file type
    if filename.endswith(".csv"):
        # Finance CSV
        if "account-statement" in filename or "revolut" in filename:
            source = "revolut"
        elif "transaction_export" in filename or "aib" in filename:
            source = "aib"
        elif "Posted Account" in file_content[:200]:
            source = "aib"
        elif "Started Date" in file_content[:200]:
            source = "revolut"
        else:
            await update.message.reply_text("Couldn't detect if this is Revolut or AIB. Please rename the file to include 'revolut' or 'aib' in the filename.")
            return

        await update.message.reply_text(f"📄 Processing {source.upper()} CSV...")
        result = process_import_csv(file_content, source)
        save_conversation("user", f"[Uploaded {source} CSV: {document.file_name}]")
        save_conversation("assistant", result)
        await update.message.reply_text(result)

    elif filename.endswith(".txt") or is_mfp_diary(file_content):
        # MFP diary text file
        if is_mfp_diary(file_content):
            await update.message.reply_text("🍽️ MFP diary detected, parsing...")
            result = process_import_mfp(file_content)
            save_conversation("user", f"[Uploaded MFP diary: {document.file_name}]")
            save_conversation("assistant", result)
            await update.message.reply_text(result)
        else:
            await update.message.reply_text("I can accept finance CSVs (Revolut/AIB) or MFP diary exports. This doesn't look like either.")

    else:
        await update.message.reply_text("I accept CSV files (Revolut/AIB) or MFP diary text files. Upload one of those!")