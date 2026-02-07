from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List

import json

from config import LEDGER_FILE


@dataclass(frozen=True)
class LedgerEntry:
    amount: float
    label: str
    timestamp: str
    user_id: int


def _parse_timestamp(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def load_ledger_entries(ledger_file: Path = LEDGER_FILE) -> List[LedgerEntry]:
    if not ledger_file.exists():
        return []
    entries: List[LedgerEntry] = []
    for line in ledger_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        data = json.loads(line)
        entries.append(
            LedgerEntry(
                amount=float(data.get("amount", 0)),
                label=str(data.get("label", "")),
                timestamp=str(data.get("timestamp", "")),
                user_id=int(data.get("user_id", 0)),
            )
        )
    return entries


def today_total_spent(entries: Iterable[LedgerEntry], today: date | None = None) -> float:
    if today is None:
        today = datetime.utcnow().date()
    total = 0.0
    for entry in entries:
        parsed = _parse_timestamp(entry.timestamp)
        if parsed and parsed.date() == today:
            total += entry.amount
    return total


def recent_daily_avg_7d(entries: Iterable[LedgerEntry], today: date | None = None) -> float:
    if today is None:
        today = datetime.utcnow().date()
    start_day = today - timedelta(days=6)
    totals: Dict[date, float] = {start_day + timedelta(days=i): 0.0 for i in range(7)}
    for entry in entries:
        parsed = _parse_timestamp(entry.timestamp)
        if not parsed:
            continue
        entry_day = parsed.date()
        if start_day <= entry_day <= today:
            totals[entry_day] += entry.amount
    return sum(totals.values()) / 7


def spend_recommend_cashflow(
    current_savings: float,
    next_payday: str,
    fixed_monthly_bills: float = 0,
    min_daily_floor: float = 20,
    safety_days: int = 7,
    ledger_file: Path = LEDGER_FILE,
) -> Dict[str, object]:
    today = datetime.utcnow().date()
    payday = datetime.strptime(next_payday, "%Y-%m-%d").date()
    runway_days = max(1, (payday - today).days)
    safety_buffer = min_daily_floor * safety_days
    prorated_fixed_bills = fixed_monthly_bills * runway_days / 30
    available = max(0.0, current_savings - safety_buffer - prorated_fixed_bills)
    base = available / runway_days

    entries = load_ledger_entries(ledger_file)
    today_spent = today_total_spent(entries, today)
    avg_7d = recent_daily_avg_7d(entries, today)

    upper_bound = max(min_daily_floor, avg_7d * 1.1)
    recommended = min(max(base, min_daily_floor), upper_bound)
    notes: List[str] = [
        f"Runway days: {runway_days}.",
        "Safety buffer applied.",
    ]

    if today_spent > recommended:
        recommended -= (today_spent - recommended) * 0.2
        recommended = max(min_daily_floor, recommended)
        notes.append("Reduced for overspend today.")

    return {
        "recommended_daily_budget": round(recommended, 2),
        "runway_days": runway_days,
        "safety_buffer": round(safety_buffer, 2),
        "available": round(available, 2),
        "notes": notes[:3],
    }
