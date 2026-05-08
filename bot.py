import os

import openai
from dotenv import load_dotenv
from hindsight_client import Hindsight
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

import context as ctx
from persona import build_system_prompt, load_config

load_dotenv()

_config = load_config()
SYSTEM_PROMPT = build_system_prompt(_config)
BANK_ID = "dylan"

openai_client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
hindsight = Hindsight(base_url=os.getenv("HINDSIGHT_BASE_URL", "http://localhost:8888"))


def _recalled_context(query: str) -> str:
    try:
        results = hindsight.recall(bank_id=BANK_ID, query=query, top_k=5)
        memories = [r.content for r in results.memories if r.content]
        if not memories:
            return ""
        return "Relevant memories:\n" + "\n".join(f"- {m}" for m in memories) + "\n\n"
    except Exception:
        return ""


def _retain(content: str) -> None:
    try:
        hindsight.retain(bank_id=BANK_ID, content=content)
    except Exception:
        pass


def ask_llm(user_message: str) -> str:
    recalled = _recalled_context(user_message)
    today = ctx.today_summary_prompt()

    system = SYSTEM_PROMPT
    if recalled or today:
        system += "\n\n" + recalled + today

    history = ctx.load_today()
    messages = [{"role": "system", "content": system}] + history + [{"role": "user", "content": user_message}]

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        max_tokens=1024,
        messages=messages,
    )
    return response.choices[0].message.content


async def handle_message(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    user_text = update.message.text
    ctx.append_exchange("user", user_text)

    reply = ask_llm(user_text)
    ctx.append_exchange("assistant", reply)

    _retain(f"Dylan said: {user_text}\nAssistant replied: {reply}")

    await update.message.reply_text(reply)


async def cmd_recap(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    today = ctx.today_summary_prompt()
    if not today:
        await update.message.reply_text("Nothing logged yet today.")
        return
    reply = ask_llm(
        today + "Give me a tight recap of today: what I worked on, what moved forward, what didn't."
    )
    await update.message.reply_text(reply)


async def cmd_nudge(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    reply = ask_llm(
        "Based on everything you know about me and my projects, give me one honest nudge. "
        "What should I actually be doing right now?"
    )
    await update.message.reply_text(reply)


async def cmd_start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hey Dylan. What are we working on today?")


def main() -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("recap", cmd_recap))
    app.add_handler(CommandHandler("nudge", cmd_nudge))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
