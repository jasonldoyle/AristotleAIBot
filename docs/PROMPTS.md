# Prompt System

## Overview

Plato uses a monolithic prompt that assembles all action schemas and context into a single system prompt for every Claude call. This is simple and ensures Claude always has full context.

## How It Works

```
User message
    |
    v
build_system_prompt()
    |
    v
Prompt Assembly:
  - Base prompt (personality, role, guidelines)
  - Soul doc (all tiers, always included)
  - Active projects with goals
  - Today's schedule
  - Weekly template (this week + next week)
  - Scheduling rules and instructions
  - All 21 action schemas with trigger conditions
    |
    v
build_messages_with_history()
  - Last 10 conversation turns
  - Current user message appended
    |
    v
Claude Sonnet API call
```

## Prompt Components

### Base Prompt (`prompts/base.py`)
- Plato's personality: stoic mentor, direct, no-nonsense
- Soul doc entries grouped by tier (lifetime → 5yr → 2yr → 1yr → philosophy → rules)
- Active projects with slugs and current goals
- Today's date and schedule

### Action Schemas (`prompts/__init__.py`)
- All 21 actions with JSON format, parameters, and `USE WHEN` trigger conditions
- Critical rules: one action per message, JSON at start of reply, no fake actions in plain text

### Schedule Prompt (`calendar.py`)
- Injected when schedule context is built
- Contains dual-week templates (this week + next week) with all typed blocks
- Scheduling rules (12 rules covering block types, project priority, rest, gym, weekend blocks)
- Response format specification for `plan_week` action
- Active project list for category assignment

## File Structure

```
plato/prompts/
  __init__.py      — build_system_prompt(), build_messages_with_history(), ACTION_SCHEMA
  base.py          — get_base_prompt() (personality + soul doc + projects + schedule)
```

## Future Consideration

Intent-based routing (detecting domains from the message and only including relevant schemas) was considered but not implemented. The current monolithic approach works well for 21 actions. May revisit in Phase 8 (Polish) if token usage becomes an issue.
