import os
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from agent import ExpenseAgent

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_FILE = Path(__file__).resolve().parent.parent / "data" / "last_chat.txt"

agent = ExpenseAgent()


def _store_chat_id(chat_id: int) -> None:
    CHAT_FILE.parent.mkdir(parents=True, exist_ok=True)
    CHAT_FILE.write_text(str(chat_id))


def _load_chat_id() -> int | None:
    if not CHAT_FILE.exists():
        return None
    try:
        return int(CHAT_FILE.read_text().strip())
    except ValueError:
        return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat:
        _store_chat_id(update.effective_chat.id)
    await update.message.reply_text(
        "Hi! Use /add <amount> <category> [note] to track expenses."
    )


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat:
        _store_chat_id(update.effective_chat.id)
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /add <amount> <category> [note]")
        return
    amount = float(context.args[0])
    category = context.args[1]
    note = " ".join(context.args[2:])
    expense = agent.add_expense(amount, category, update.effective_user.id, note)
    await update.message.reply_text(
        f"Saved {expense.amount:.2f} to {expense.category}."
    )


async def list_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat:
        _store_chat_id(update.effective_chat.id)
    await update.message.reply_text(
        "Listing is not implemented yet. Send messages like \"Lunch 12.5\" to log."
    )


async def log_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat:
        _store_chat_id(update.effective_chat.id)
    if not update.message or not update.message.text:
        return
    parsed = agent.parse_message(update.message.text)
    if not parsed:
        await update.message.reply_text(
            "Send messages like \"Lunch 12.5\" to log expenses."
        )
        return
    agent.add_expense(parsed.amount, parsed.category, update.effective_user.id)
    await update.message.reply_text(
        f"Logged {parsed.amount:.2f} to {parsed.category}."
    )


async def daily_summary(app: Application) -> None:
    chat_id = _load_chat_id()
    if not chat_id:
        return
    await app.bot.send_message(
        chat_id=chat_id,
        text="Daily reminder: log today's expenses by sending \"Lunch 12.5\".",
    )


def main() -> None:
    if not TOKEN:
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN environment variable")
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add))
    application.add_handler(CommandHandler("list", list_expenses))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, log_message))

    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(daily_summary, "cron", hour=20, args=[application])
    scheduler.start()

    application.run_polling()


if __name__ == "__main__":
    main()
