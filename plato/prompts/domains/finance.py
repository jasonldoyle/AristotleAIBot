"""
Finance domain — spending, budgets, savings.
"""

from datetime import datetime
from plato.db import get_monthly_summary, check_budget_alerts


def get_action_schemas() -> str:
    return """
### FINANCE ACTIONS:

**FINANCE REVIEW** - Spending/savings summary
```json
{"action": "finance_review", "year": 2026, "month": 2}
```

**SET BUDGET** - Monthly spending limit for a category
```json
{"action": "set_budget", "category": "takeaway", "monthly_limit": 100.00}
```

### FINANCE NOTES:
- Jason uploads Revolut and AIB CSVs monthly — these are parsed and stored automatically
- He can also paste MFP printable diary text — this gets parsed into daily nutrition logs
- His dynasty goal requires aggressive saving — challenge him if spending is loose"""


def get_context() -> str:
    """Build finance context with current month summary."""
    try:
        now = datetime.now()
        summary = get_monthly_summary(now.year, now.month)

        if summary["transaction_count"] == 0:
            return ""

        context = f"\n## FINANCE — {summary['month']}\n"
        context += f"  Income: €{summary['total_income']:,.2f} | Spending: €{summary['total_spending']:,.2f}\n"
        context += f"  Net: €{summary['net']:,.2f} | Savings rate: {summary['savings_rate']}%\n"

        if summary["by_category"]:
            top_3 = list(summary["by_category"].items())[:3]
            context += f"  Top spend: {', '.join(f'{cat} €{amt:,.2f}' for cat, amt in top_3)}\n"

        alerts = check_budget_alerts(now.year, now.month)
        if alerts:
            for a in alerts:
                icon = "🔴" if a["status"] == "over" else "🟡"
                context += f"  {icon} {a['category']}: €{a['spent']:.2f}/€{a['limit']:.2f}\n"

        return context
    except Exception:
        return ""
