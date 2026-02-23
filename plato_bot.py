"""
Plato Bot — Entry Point
Personal AI mentor for Jason. Built with stoic wisdom and accountability.
"""

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from plato.config import TELEGRAM_TOKEN, logger
from plato.handlers import handle_message, start, clear_history


def main() -> None:
    """Start the bot."""
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear_history))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Plato is starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
