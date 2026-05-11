import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

import db

load_dotenv()


async def cmd_start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Ready.\n/log <message> — record what's happening\n/schedule — view today's plan"
    )


async def cmd_log(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    parts = update.message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await update.message.reply_text("Usage: /log <message>")
        return
    time_str = db.add_log(parts[1].strip())
    await update.message.reply_text(f"Logged at {time_str}.")


async def cmd_schedule(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    day = db.current_day()
    plans = db.get_plans(day)
    if not plans:
        await update.message.reply_text(f"No plan for {day}.")
        return
    lines = [f"Schedule — {day}\n"]
    for row in plans:
        lines.append(f"{row['start_time']}–{row['end_time']}  {row['title']}")
    await update.message.reply_text("\n".join(lines))


def main() -> None:
    db.init_db()
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("log", cmd_log))
    app.add_handler(CommandHandler("schedule", cmd_schedule))
    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
