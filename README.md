# Telegram Expense Agent

Minimal Telegram bot for tracking expenses with local JSON storage.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a bot token with BotFather and run:

```bash
export TELEGRAM_BOT_TOKEN=your_token
export DAILY_BUDGET=50
python src/bot.py
```

Commands:
- `/add <amount> <category> [note]`
- `/list`
- `/recommend`

Daily summary is sent at 20:00 UTC.
