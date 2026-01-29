import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "expenses.json"


@dataclass
class Expense:
    amount: float
    category: str
    note: str
    timestamp: str


class ExpenseAgent:
    def __init__(self, data_file: Path = DATA_FILE) -> None:
        self.data_file = data_file
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.data_file.exists():
            self._write_data([])

    def add_expense(self, amount: float, category: str, note: str = "") -> Expense:
        expense = Expense(
            amount=amount,
            category=category,
            note=note,
            timestamp=datetime.utcnow().isoformat(),
        )
        data = self._read_data()
        data.append(expense.__dict__)
        self._write_data(data)
        return expense

    def list_expenses(self) -> List[Expense]:
        return [Expense(**item) for item in self._read_data()]

    def spend_recommend(self, budget: float) -> str:
        expenses = self._read_data()
        total = sum(item.get("amount", 0) for item in expenses)
        remaining = budget - total
        if remaining <= 0:
            return "You have no remaining budget today. Consider pausing spending."
        avg = total / max(len(expenses), 1)
        return (
            f"Total spent: {total:.2f}. Remaining: {remaining:.2f}. "
            f"Average spend per entry: {avg:.2f}."
        )

    def _read_data(self) -> List[Dict[str, Any]]:
        if not self.data_file.exists():
            return []
        return json.loads(self.data_file.read_text())

    def _write_data(self, data: List[Dict[str, Any]]) -> None:
        self.data_file.write_text(json.dumps(data, indent=2))
