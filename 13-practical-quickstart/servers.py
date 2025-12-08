"""Minimal MCP stub servers powered by DictToolServer."""

import argparse
import sys
from pathlib import Path
from typing import Dict

sys.path.append(str(Path(__file__).resolve().parents[1]))

from universal_agent_tools.patterns import DictToolServer, ToolHandler

BILLING_DB: Dict[str, dict] = {
    "user123": {"balance": 100.0, "status": "active"},
    "user456": {"balance": -50.0, "status": "overdue"},
}


def billing_handlers() -> Dict[str, ToolHandler]:
    return {
        "get_balance": lambda args: BILLING_DB.get(args.get("user_id", ""), {"balance": 0, "status": "unknown"}),
        "process_payment": lambda args: _process_payment(args.get("user_id"), args.get("amount", 0)),
    }


def _process_payment(user_id: str, amount: float):
    if user_id not in BILLING_DB:
        return "User not found"
    BILLING_DB[user_id]["balance"] += amount
    return {"message": f"Payment processed: +${amount}", "balance": BILLING_DB[user_id]["balance"]}


def tech_handlers() -> Dict[str, ToolHandler]:
    return {
        "diagnose": lambda args: {
            "status": "investigating",
            "steps": ["Collect logs", "Restart service", "Escalate if persistent"],
        }
    }


def account_handlers() -> Dict[str, ToolHandler]:
    return {
        "reset_password": lambda args: f"Password reset link sent to {args.get('email', 'user email')}",
        "unlock_account": lambda args: "Account unlocked",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", choices=["billing", "tech", "account"], required=True)
    args = parser.parse_args()

    mapping = {
        "billing": ("billing-mcp", billing_handlers),
        "tech": ("tech-mcp", tech_handlers),
        "account": ("account-mcp", account_handlers),
    }

    server_name, handlers_fn = mapping[args.server]
    DictToolServer(server_name, handlers_fn()).run_sync()


if __name__ == "__main__":
    main()
