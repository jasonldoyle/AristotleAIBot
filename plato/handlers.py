import json
from telegram import Update
from telegram.ext import ContextTypes
from plato.config import ALLOWED_USER_ID, anthropic_client, logger
from plato.db import save_conversation, clear_conversations
from plato.prompts import build_system_prompt, build_messages_with_history
from plato.actions import process_action


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

    system_prompt = build_system_prompt()
    messages = build_messages_with_history(user_message)

    response = anthropic_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=system_prompt,
        messages=messages
    )

    reply = response.content[0].text

    # Process JSON action block if present
    action_result = None
    if "```json" in reply:
        try:
            json_start = reply.index("```json") + 7
            json_end = reply.index("```", json_start)
            json_str = reply[json_start:json_end].strip()
            action_data = json.loads(json_str)

            action_result = process_action(action_data)
            logger.info(f"Action result: {action_result}")

            # Strip the JSON block from the reply
            reply = reply[:reply.index("```json")] + reply[json_end + 3:]
            reply = reply.strip()
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse action JSON: {e}")

    # Prepend action status if there was one
    if action_result:
        reply = f"[{action_result}]\n\n{reply}"

    # Save assistant response to history
    save_conversation("assistant", reply)

    # Telegram has a 4096 char limit — split long messages
    if len(reply) <= 4096:
        await update.message.reply_text(reply)
    else:
        # Split on double newlines to keep logical chunks together
        chunks = []
        current = ""
        for paragraph in reply.split("\n\n"):
            if len(current) + len(paragraph) + 2 > 4000:
                if current:
                    chunks.append(current.strip())
                current = paragraph
            else:
                current = current + "\n\n" + paragraph if current else paragraph
        if current:
            chunks.append(current.strip())

        for chunk in chunks:
            # Final safety split if a single paragraph is > 4096
            while len(chunk) > 4096:
                await update.message.reply_text(chunk[:4096])
                chunk = chunk[4096:]
            if chunk:
                await update.message.reply_text(chunk)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    if update.effective_user.id != ALLOWED_USER_ID:
        return
    await update.message.reply_text("Plato is ready. What have you been working on?")


async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /clear command - clear conversation history."""
    if update.effective_user.id != ALLOWED_USER_ID:
        return

    clear_conversations()
    await update.message.reply_text("Conversation history cleared. Fresh start.")
