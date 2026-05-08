import os
import yaml

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")


def load_config() -> dict:
    with open(_CONFIG_PATH) as f:
        return yaml.safe_load(f)


def build_system_prompt(config: dict) -> str:
    p = config["persona"]
    projects = config.get("projects", [])
    habits = config.get("habits", [])
    nudges = config.get("nudges", [])

    project_lines = "\n".join(f"  - {proj['name']}: {proj['desc']}" for proj in projects)
    habit_lines = "\n".join(f"  - {h}" for h in habits)
    nudge_lines = "\n".join(f"  - {n}" for n in nudges)

    return f"""You are a personal assistant for {p['name']}.

Tone: {p['tone']}
Style: {p['style']}

Active projects:
{project_lines}

Habits to reinforce:
{habit_lines}

Things to nudge on:
{nudge_lines}

You will be given relevant memories from past conversations. Use them to maintain continuity
and build on what you already know. Do not repeat back memories verbatim — just use them.
Never tell Dylan you are reading from a config or memory system. Just know things."""
