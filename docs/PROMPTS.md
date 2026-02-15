# Prompt System

## Overview

Plato uses an intent-based prompt system that assembles only the relevant domain schemas and context for each message. This reduces token usage by 50-70% compared to the previous monolithic approach.

## How It Works

```
User message
    |
    v
Intent Detection (keyword matching)
    |
    v
Domain Selection (e.g., fitness + schedule)
    |
    v
Prompt Assembly:
  - Base prompt (always included)
  - Soul doc (always included)
  - Today's schedule brief (always included)
  - Overdue tasks brief (always included)
  - Domain-specific action schemas (only for detected domains)
  - Domain-specific context (only for detected domains)
```

## Domain Keyword Mapping

| Domain | Keywords |
|--------|----------|
| fitness | workout, gym, weight, training, block, lift, squat, bench, nutrition, mfp, skincare, cycling, progress photos, exercise, bulk, cut, protein, calories |
| schedule | plan, week, schedule, calendar, approve, audrey time, event |
| projects | project, log, work, coding, nitrogen, glowbook, cfa, plato, leetcode |
| finance | spend, budget, money, finance, revolut, aib, csv, saving |
| admin | task, todo, reminder, birthday, recurring, laundry, overdue |
| ideas | idea, park, parked |

## Assembly Rules

1. **Always included**: base prompt + soul doc + current date/time
2. **Always included as brief context**: today's schedule, overdue tasks
3. **Included per detected domain**: action schemas + full context data
4. **Fallback**: if no domain detected (general chat), include only base + always-on contexts
5. **Multi-domain**: if message touches multiple domains, include all relevant ones

## File Structure

```
plato/prompts/
  __init__.py      - build_system_prompt(message), build_messages_with_history()
  base.py          - Core personality, role, guidelines
  intent.py        - detect_domains(message) -> set of domain names
  context.py       - Context builders (schedule, overdue tasks, etc.)
  domains/
    __init__.py    - Domain registry and get_domain_prompt()
    fitness.py     - Fitness actions + context
    schedule.py    - Schedule actions + context
    projects.py    - Project actions + context
    finance.py     - Finance actions + context
    admin.py       - Admin/task actions + context
    ideas.py       - Idea actions + context
```

## Expected Impact

- Typical request: ~5-8KB prompt (down from ~16-20KB)
- Focused context produces better Claude responses
- Domain isolation makes adding new actions easier
