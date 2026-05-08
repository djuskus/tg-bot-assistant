import json
import os
from datetime import date

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
USAGE_FILE = os.path.join(DATA_DIR, "usage.json")


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
    today = date.today().isoformat()
    usage = {}
    if os.path.exists(USAGE_FILE):
        with open(USAGE_FILE) as f:
            usage = json.load(f)
    day = usage.setdefault(today, {"prompt": 0, "completion": 0})
    day["prompt"] += prompt_tokens
    day["completion"] += completion_tokens
    with open(USAGE_FILE, "w") as f:
        json.dump(usage, f, indent=2)


def get_usage() -> dict:
    if not os.path.exists(USAGE_FILE):
        return {}
    with open(USAGE_FILE) as f:
        return json.load(f)


def today_summary_prompt() -> str:
    log = load_today()
    if not log:
        return ""
    lines = [f"{e['role'].upper()}: {e['content']}" for e in log]
    return "Today's conversation so far:\n" + "\n".join(lines) + "\n\n---\n\n"
