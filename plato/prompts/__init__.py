"""
Prompt orchestrator — builds system prompts based on message intent.
"""

import logging
from plato.db import get_recent_conversations
from plato.prompts.base import get_base_prompt, get_guidelines
from plato.prompts.intent import detect_domains
from plato.prompts.context import get_today_schedule_brief, get_overdue_tasks_brief
from plato.prompts.domains import get_domain_prompt

logger = logging.getLogger(__name__)


def build_system_prompt(message: str = "", schedule_context: str = "") -> str:
    """Build Plato's system prompt with only relevant domain context.

    Args:
        message: The user's message (used for intent detection).
        schedule_context: Extra schedule context (e.g., week planning prompt).
    """
    parts = []

    # Always included: base prompt with personality + soul doc
    parts.append(get_base_prompt())

    # Always included: brief ambient context
    today_schedule = get_today_schedule_brief()
    if today_schedule:
        parts.append(today_schedule)

    overdue = get_overdue_tasks_brief()
    if overdue:
        parts.append(overdue)

    # Detect which domains are relevant
    domains = detect_domains(message)

    # If schedule_context is provided (plan week flow), always include schedule domain
    if schedule_context:
        domains.add("schedule")

    logger.info(f"Detected domains: {domains or 'none (general chat)'}")

    if domains:
        parts.append("\n## YOUR CAPABILITIES\nWhen Jason messages you, determine the intent and respond with the appropriate JSON action block followed by your message.\n\n### ACTIONS YOU CAN TAKE:")

        for domain in sorted(domains):
            domain_prompt = get_domain_prompt(domain)
            if domain_prompt:
                parts.append(domain_prompt)

    # Guidelines always included
    parts.append(get_guidelines())

    # Extra schedule context (week planning prompt from plato_calendar.py)
    if schedule_context:
        parts.append(schedule_context)

    return "\n".join(parts)


def build_messages_with_history(user_message: str) -> list[dict]:
    """Build message list including conversation history."""
    history = get_recent_conversations(limit=10)

    messages = []
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": user_message})

    return messages
