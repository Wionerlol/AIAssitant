import json
from datetime import datetime, timedelta
from pathlib import Path

from finance import (
    LedgerEntry,
    recent_daily_avg_7d,
    spend_recommend_cashflow,
    today_total_spent,
)


def write_ledger(path: Path, entries: list[LedgerEntry]) -> None:
    lines = [
        {
            "amount": entry.amount,
            "label": entry.label,
            "timestamp": entry.timestamp,
            "user_id": entry.user_id,
        }
        for entry in entries
    ]
    path.write_text("\n".join(json.dumps(item) for item in lines))


def test_next_payday_today(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text("")
    today = datetime.utcnow().date().strftime("%Y-%m-%d")
    result = spend_recommend_cashflow(
        current_savings=100,
        next_payday=today,
        ledger_file=ledger,
    )
    assert result["runway_days"] == 1
    assert result["recommended_daily_budget"] >= 20


def test_small_savings_and_avg(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    today = datetime.utcnow().date()
    entries = [
        LedgerEntry(5, "coffee", datetime.utcnow().isoformat(), 1),
        LedgerEntry(10, "lunch", (datetime.utcnow() - timedelta(days=1)).isoformat(), 1),
    ]
    write_ledger(ledger, entries)
    total_today = today_total_spent(entries, today)
    avg_7d = recent_daily_avg_7d(entries, today)
    assert total_today == 5
    assert avg_7d > 0

    result = spend_recommend_cashflow(
        current_savings=10,
        next_payday=(today + timedelta(days=5)).strftime("%Y-%m-%d"),
        ledger_file=ledger,
    )
    assert result["available"] == 0


def test_huge_fixed_bills(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text("")
    today = datetime.utcnow().date()
    result = spend_recommend_cashflow(
        current_savings=200,
        next_payday=(today + timedelta(days=10)).strftime("%Y-%m-%d"),
        ledger_file=ledger,
        fixed_monthly_bills=10000,
    )
    assert result["available"] == 0
    assert result["recommended_daily_budget"] >= 20
