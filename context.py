import json
import os
import time
from datetime import date, datetime, timezone

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
USAGE_FILE = os.path.join(DATA_DIR, "usage.json")

# GPT-4o pricing per token
_COST_PER_PROMPT_TOKEN = 2.50 / 1_000_000
_COST_PER_COMPLETION_TOKEN = 10.00 / 1_000_000


def tokens_to_usd(prompt: int, completion: int) -> float:
    return prompt * _COST_PER_PROMPT_TOKEN + completion * _COST_PER_COMPLETION_TOKEN


def _today_path() -> str:
    os.makedirs(DATA_DIR, exist_ok=True)
    return os.path.join(DATA_DIR, f"{date.today().isoformat()}.json")


def load_today() -> list[dict]:
    path = _today_path()
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)


def append_exchange(role: str, content: str) -> None:
    log = load_today()
    log.append({"role": role, "content": content})
    with open(_today_path(), "w") as f:
        json.dump(log, f, indent=2)


def track_usage(prompt_tokens: int, completion_tokens: int) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    entries = []
    if os.path.exists(USAGE_FILE):
        with open(USAGE_FILE) as f:
            entries = json.load(f)
    entries.append({
        "ts": time.time(),
        "prompt": prompt_tokens,
        "completion": completion_tokens,
    })
    with open(USAGE_FILE, "w") as f:
        json.dump(entries, f, indent=2)


def get_usage_summary(budget_usd: float) -> str:
    if not os.path.exists(USAGE_FILE):
        return "No usage tracked yet."

    with open(USAGE_FILE) as f:
        entries = json.load(f)

    now = time.time()
    today_str = date.today().isoformat()

    hour_p = hour_c = 0
    day_p = day_c = 0
    total_p = total_c = 0

    for e in entries:
        p, c, ts = e["prompt"], e["completion"], e["ts"]
        total_p += p
        total_c += c
        if datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat() == today_str:
            day_p += p
            day_c += c
        if now - ts <= 3600:
            hour_p += p
            hour_c += c

    total_cost = tokens_to_usd(total_p, total_c)
    day_cost = tokens_to_usd(day_p, day_c)
    hour_cost = tokens_to_usd(hour_p, hour_c)
    remaining = budget_usd - total_cost

    lines = [
        f"Last hour:  ${hour_cost:.4f}  ({hour_p+hour_c:,} tokens)",
        f"Today:      ${day_cost:.4f}  ({day_p+day_c:,} tokens)",
        f"Total:      ${total_cost:.4f}  ({total_p+total_c:,} tokens)",
        f"",
        f"Budget:     ${budget_usd:.2f}",
        f"Remaining:  ${remaining:.4f}",
    ]
    return "\n".join(lines)


def today_summary_prompt() -> str:
    log = load_today()
    if not log:
        return ""
    lines = [f"{e['role'].upper()}: {e['content']}" for e in log]
    return "Today's conversation so far:\n" + "\n".join(lines) + "\n\n---\n\n"
