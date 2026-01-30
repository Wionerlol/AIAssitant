from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import json
import os

from config import LEDGER_FILE
from llm.kimi_client import KimiClient
from tools.cashflow import spend_recommend_cashflow


@dataclass
class Expense:
    amount: float
    category: str
    note: str
    timestamp: str


class ExpenseAgent:
    def __init__(self, ledger_file: Path = LEDGER_FILE) -> None:
        self.ledger_file = ledger_file
        self.ledger_file.parent.mkdir(parents=True, exist_ok=True)
        self.ledger_file.touch(exist_ok=True)
        self.client = KimiClient()

    def add_expense(self, amount: float, label: str, user_id: int, note: str = "") -> Expense:
        expense = Expense(
            amount=amount,
            category=label,
            note=note,
            timestamp=datetime.utcnow().isoformat(),
        )
        self._append_ledger(
            {
                "amount": expense.amount,
                "label": expense.category,
                "timestamp": expense.timestamp,
                "user_id": user_id,
            }
        )
        return expense

    def parse_message(self, text: str) -> Expense | None:
        parts = text.strip().split()
        if len(parts) < 2:
            return None
        *label_parts, amount_text = parts
        try:
            amount = float(amount_text)
        except ValueError:
            return None
        label = " ".join(label_parts)
        if not label:
            return None
        return Expense(
            amount=amount,
            category=label,
            note="",
            timestamp=datetime.utcnow().isoformat(),
        )

    def is_recommendation_message(self, text: str) -> bool:
        lowered = text.lower()
        keywords = ["recommend", "summary", "budget", "spend", "advice", "建议", "预算", "总结"]
        return any(keyword in lowered for keyword in keywords)

    def handle_recommendation(self, message: str) -> str:
        tools = self._tool_schemas()
        messages = [
            {"role": "system", "content": "You are a finance assistant."},
            {"role": "user", "content": message},
        ]
        try:
            response = self.client.chat(messages, tools=tools)
            reply = self._handle_tool_calls(response, messages, tools)
            return reply
        except Exception:
            fallback = self._fallback_recommendation()
            return json.dumps(fallback, ensure_ascii=False)

    def _handle_tool_calls(
        self, response: Dict[str, Any], messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]
    ) -> str:
        message = response["choices"][0]["message"]
        tool_calls = message.get("tool_calls") or []
        if tool_calls:
            messages.append(
                {
                    "role": "assistant",
                    "content": message.get("content", ""),
                    "tool_calls": tool_calls,
                }
            )
            for call in tool_calls:
                result = self._execute_tool(call)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.get("id"),
                        "name": call["function"]["name"],
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )
            follow_up = self.client.chat(messages, tools=tools)
            return follow_up["choices"][0]["message"].get("content", "")
        return message.get("content", "")

    def _execute_tool(self, call: Dict[str, Any]) -> Dict[str, Any]:
        name = call["function"]["name"]
        arguments = json.loads(call["function"].get("arguments", "{}"))
        if name == "spend_recommend_cashflow":
            return spend_recommend_cashflow(**arguments)
        if name == "get_time":
            return {"now": datetime.utcnow().isoformat()}
        raise ValueError(f"Unknown tool: {name}")

    def _tool_schemas(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "spend_recommend_cashflow",
                    "description": "Recommend a daily budget based on cashflow.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "current_savings": {"type": "number"},
                            "next_payday": {"type": "string", "description": "YYYY-MM-DD"},
                            "fixed_monthly_bills": {"type": "number", "default": 0},
                            "min_daily_floor": {"type": "number", "default": 20},
                            "safety_days": {"type": "integer", "default": 7},
                        },
                        "required": ["current_savings", "next_payday"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_time",
                    "description": "Get current UTC time.",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
        ]

    def _fallback_recommendation(self) -> Dict[str, Any]:
        current_savings = float(os.getenv("CURRENT_SAVINGS", "0"))
        next_payday = os.getenv("NEXT_PAYDAY", datetime.utcnow().date().isoformat())
        fixed_monthly_bills = float(os.getenv("FIXED_MONTHLY_BILLS", "0"))
        min_daily_floor = float(os.getenv("MIN_DAILY_FLOOR", "20"))
        safety_days = int(os.getenv("SAFETY_DAYS", "7"))
        return spend_recommend_cashflow(
            current_savings=current_savings,
            next_payday=next_payday,
            fixed_monthly_bills=fixed_monthly_bills,
            min_daily_floor=min_daily_floor,
            safety_days=safety_days,
        )

    def _append_ledger(self, entry: Dict[str, Any]) -> None:
        with self.ledger_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
