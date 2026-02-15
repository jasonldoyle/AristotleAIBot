"""
Domain registry — maps domain names to their prompt modules.
"""

from plato.prompts.domains import fitness, schedule, projects, finance, admin, ideas

DOMAIN_MODULES = {
    "fitness": fitness,
    "schedule": schedule,
    "projects": projects,
    "finance": finance,
    "admin": admin,
    "ideas": ideas,
}


def get_domain_prompt(domain: str) -> str:
    """Get the full prompt section (schemas + context) for a domain."""
    module = DOMAIN_MODULES.get(domain)
    if not module:
        return ""

    parts = []
    schemas = module.get_action_schemas()
    if schemas:
        parts.append(schemas)

    context = module.get_context()
    if context:
        parts.append(context)

    return "\n".join(parts)
