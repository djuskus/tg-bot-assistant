import json
import os
from datetime import date

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


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


def today_summary_prompt() -> str:
    log = load_today()
    if not log:
        return ""
    lines = [f"{e['role'].upper()}: {e['content']}" for e in log]
    return "Today's conversation so far:\n" + "\n".join(lines) + "\n\n---\n\n"
