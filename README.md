# Telegram Expense Agent

Minimal Telegram bot for tracking expenses with local JSONL storage.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a bot token with BotFather and run:

```bash
export TELEGRAM_BOT_TOKEN=your_token
python src/bot.py
```

Commands:
- `/add <amount> <category> [note]`
- `/list`

You can also send a plain message like `午饭 12.5` to log an expense to `data/ledger.jsonl`.

Daily reminder is sent at 20:00 UTC.
