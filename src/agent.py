from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import json

LEDGER_FILE = Path(__file__).resolve().parent.parent / "data" / "ledger.jsonl"


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

    def _append_ledger(self, entry: Dict[str, Any]) -> None:
        with self.ledger_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
