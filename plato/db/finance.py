"""
Finance tracking database operations.
Handles CSV parsing for Revolut and AIB, transaction storage, and reporting.
"""

import csv
import io
from datetime import datetime, timedelta
from plato.config import supabase, logger


# ============== CATEGORY MAPPING ==============
# Maps description keywords to categories

CATEGORY_RULES = [
    # Income (check first)
    (["citco funds"], "salary"),
    
    # Transfers (check early)
    (["revolut**8820", "revolut"], "transfer"),
    
    # Subscriptions (before transport, to catch "uber one" correctly)
    (["uber   *one", "uber one"], "subscriptions"),
    (["github", "railway", "anthropic", "claude", "openai"], "dev_tools"),
    (["apple.com", "spotify", "netflix", "disney", "youtube"], "subscriptions"),
    (["zoho", "gomo", "lets host", "post publi"], "subscriptions"),
    
    # Food & Drink
    (["spar", "aldi", "lidl", "tesco", "dunnes", "musgrave", "supervalu", "centra"], "groceries"),
    (["just eat", "domino", "mcdonald", "burger", "subway", "apache"], "takeaway"),
    (["cafe", "coffee", "starbucks", "costa", "insomnia", "grainger"], "coffee_eating_out"),
    (["restaurant", "wok on", "o briens", "seven wonders", "derreen", "ollie"], "coffee_eating_out"),
    
    # Transport
    (["luas", "dublin bus", "leap", "irish rail", "dart"], "transport"),
    (["maxol", "circle k", "applegreen", "topaz", "fuel"], "fuel"),
    (["uber", "bolt", "taxi", "freenow"], "transport"),
    (["car park", "parking"], "transport"),
    
    # Housing
    (["westwood leopa", "rent"], "rent"),
    (["electric", "energia", "bord gais", "sse airtricity"], "utilities"),
    
    # Health & Fitness
    (["west wood club", "gym", "decathlon", "elvery"], "fitness"),
    (["pharmacy", "blackglen phar"], "health"),
    
    # Shopping
    (["tk maxx", "h&m", "hm ie", "zara", "penneys", "primark"], "clothing"),
    (["smyths", "powercity", "currys", "argos", "amazon"], "shopping"),
    (["dockers", "jackma"], "shopping"),
]


def categorise_transaction(description: str) -> str:
    """Auto-categorise a transaction based on description keywords."""
    desc_lower = description.lower()
    for keywords, category in CATEGORY_RULES:
        for keyword in keywords:
            if keyword in desc_lower:
                return category
    return "other"


# ============== CSV PARSERS ==============

def parse_revolut_csv(csv_content: str) -> list[dict]:
    """Parse Revolut CSV export into transaction dicts."""
    transactions = []
    reader = csv.DictReader(io.StringIO(csv_content))
    
    for row in reader:
        # Skip non-completed transactions
        if row.get("State", "").strip() != "COMPLETED":
            continue
        
        try:
            # Parse date - format: "2026-01-31 15:35:57"
            date_str = row["Completed Date"].strip()[:10]
            date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
            
            description = row["Description"].strip()
            amount = float(row["Amount"].strip())
            fee = float(row.get("Fee", "0").strip() or "0")
            balance = float(row["Balance"].strip()) if row.get("Balance", "").strip() else None
            
            # Apply fee as separate transaction if non-zero
            category = categorise_transaction(description)
            is_transfer = category == "transfer"
            
            transactions.append({
                "date": date,
                "description": description,
                "amount": amount,
                "category": category,
                "source": "revolut",
                "original_description": description,
                "balance_after": balance,
                "is_transfer": is_transfer,
            })
            
            if fee and fee != 0:
                transactions.append({
                    "date": date,
                    "description": f"Fee: {description}",
                    "amount": -abs(fee),
                    "category": "fees",
                    "source": "revolut",
                    "original_description": f"Fee for {description}",
                    "balance_after": None,
                    "is_transfer": False,
                })
        
        except (ValueError, KeyError) as e:
            logger.error(f"Skipping Revolut row: {e} — {row}")
            continue
    
    return transactions


def parse_aib_csv(csv_content: str) -> list[dict]:
    """Parse AIB CSV export into transaction dicts."""
    transactions = []
    reader = csv.DictReader(io.StringIO(csv_content))
    
    for row in reader:
        try:
            description = row.get("Description", row.get(" Description", "")).strip().strip('"')
            debit = row.get("Debit Amount", row.get(" Debit Amount", "")).strip()
            credit = row.get("Credit Amount", row.get(" Credit Amount", "")).strip()
            date_str = row.get("Posted Transactions Date", row.get(" Posted Transactions Date", "")).strip()
            balance = row.get("Balance", row.get("Balance", "")).strip()
            
            # Skip supplementary FX rows (exchange rates, fee info, etc.)
            if not debit and (not credit or credit == "0.00"):
                continue
            
            # Skip "Interest Rate" and "Lending @" info rows
            if description.startswith("Interest Rate") or description.startswith("Lending @"):
                continue
            
            # Skip FX detail rows like "10.00 USD@", "1.177856", "INCL FX FEE"
            if "USD@" in description or "INCL FX FEE" in description:
                continue
            try:
                float(description)
                continue  # Skip pure number rows (exchange rates)
            except ValueError:
                pass
            
            # Parse date - format: "04/02/26"
            date = datetime.strptime(date_str, "%d/%m/%y").strftime("%Y-%m-%d")
            
            # Determine amount
            if debit:
                amount = -abs(float(debit))
            elif credit and float(credit) > 0:
                amount = float(credit)
            else:
                continue
            
            balance_after = float(balance) if balance else None
            
            category = categorise_transaction(description)
            is_transfer = category == "transfer"
            
            transactions.append({
                "date": date,
                "description": description,
                "amount": amount,
                "category": category,
                "source": "aib",
                "original_description": description,
                "balance_after": balance_after,
                "is_transfer": is_transfer,
            })
        
        except (ValueError, KeyError) as e:
            logger.error(f"Skipping AIB row: {e} — {row}")
            continue
    
    return transactions


# ============== DATABASE OPERATIONS ==============

def import_transactions(transactions: list[dict]) -> dict:
    """Import parsed transactions into the database. Returns import stats."""
    imported = 0
    skipped = 0
    
    for txn in transactions:
        try:
            supabase.table("transactions").insert(txn).execute()
            imported += 1
        except Exception as e:
            if "duplicate" in str(e).lower() or "23505" in str(e):
                skipped += 1
            else:
                logger.error(f"Failed to insert transaction: {e}")
                skipped += 1
    
    return {"imported": imported, "skipped": skipped}


def get_transactions_for_month(year: int, month: int) -> list[dict]:
    """Fetch all transactions for a given month."""
    start = f"{year}-{month:02d}-01"
    if month == 12:
        end = f"{year + 1}-01-01"
    else:
        end = f"{year}-{month + 1:02d}-01"
    
    result = supabase.table("transactions").select("*").gte("date", start).lt("date", end).eq("is_transfer", False).order("date", desc=True).execute()
    return result.data


def get_spending_by_category(year: int, month: int) -> dict:
    """Calculate spending by category for a month."""
    txns = get_transactions_for_month(year, month)
    
    by_category = {}
    for txn in txns:
        if txn["amount"] < 0:  # spending only
            cat = txn["category"] or "other"
            by_category[cat] = by_category.get(cat, 0) + abs(txn["amount"])
    
    # Round values
    return {k: round(v, 2) for k, v in sorted(by_category.items(), key=lambda x: x[1], reverse=True)}


def get_monthly_summary(year: int, month: int) -> dict:
    """Calculate comprehensive monthly finance summary."""
    txns = get_transactions_for_month(year, month)
    
    income = sum(t["amount"] for t in txns if t["amount"] > 0)
    spending = sum(abs(t["amount"]) for t in txns if t["amount"] < 0)
    net = income - spending
    savings_rate = (net / income * 100) if income > 0 else 0
    by_category = get_spending_by_category(year, month)
    
    return {
        "month": f"{year}-{month:02d}",
        "total_income": round(income, 2),
        "total_spending": round(spending, 2),
        "net": round(net, 2),
        "savings_rate": round(savings_rate, 1),
        "by_category": by_category,
        "transaction_count": len(txns),
    }


def get_budget_limits() -> dict:
    """Fetch all budget limits as {category: limit}."""
    result = supabase.table("budget_limits").select("*").execute()
    return {row["category"]: float(row["monthly_limit"]) for row in result.data}


def set_budget_limit(category: str, monthly_limit: float) -> None:
    """Set or update a budget limit for a category."""
    supabase.table("budget_limits").upsert({
        "category": category,
        "monthly_limit": monthly_limit
    }, on_conflict="category").execute()


def check_budget_alerts(year: int, month: int) -> list[dict]:
    """Check which categories are over or near budget."""
    limits = get_budget_limits()
    if not limits:
        return []
    
    spending = get_spending_by_category(year, month)
    alerts = []
    
    for category, limit in limits.items():
        spent = spending.get(category, 0)
        pct = (spent / limit * 100) if limit > 0 else 0
        
        if pct >= 100:
            alerts.append({
                "category": category,
                "spent": spent,
                "limit": limit,
                "pct": round(pct, 1),
                "status": "over"
            })
        elif pct >= 80:
            alerts.append({
                "category": category,
                "spent": spent,
                "limit": limit,
                "pct": round(pct, 1),
                "status": "warning"
            })
    
    return alerts


def update_transaction_category(transaction_id: str, new_category: str) -> bool:
    """Manually re-categorise a transaction."""
    try:
        supabase.table("transactions").update({"category": new_category}).eq("id", transaction_id).execute()
        return True
    except Exception:
        return False