"""
Plato Bot v3 — Entry Point
Personal AI mentor for Jason. Built with stoic wisdom and accountability.
"""

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from plato.config import TELEGRAM_TOKEN, logger
from plato.handlers import handle_message, handle_document, start, status, clear_history
from plato.nudges import check_for_nudges


def main() -> None:
    """Start the bot."""
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("clear", clear_history))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # Proactive nudge check — runs every 5 minutes
    job_queue = app.job_queue
    job_queue.run_repeating(check_for_nudges, interval=300, first=60)

    logger.info("Plato v3 is starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()