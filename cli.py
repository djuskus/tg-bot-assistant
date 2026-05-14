#!/usr/bin/env python3
import argparse
import sys
from datetime import datetime

import db


def parse_time(t: str) -> str:
    t = t.strip().lower().replace(" ", "")
    for fmt in ("%I%p", "%I:%M%p", "%H:%M"):
        try:
            return datetime.strptime(t, fmt).strftime("%H:%M")
        except ValueError:
            continue
    print(f"ERROR: couldn't parse time '{t}' — use formats like 5pm, 5:30pm, 17:00")
    sys.exit(1)


def cmd_add_block(args):
    day = args.date or db.current_day()
    start = parse_time(args.start)
    end = parse_time(args.end)
    db.add_plan(args.title, start, end, day)
    print(f"Added: {args.title}  {start}–{end}  ({day})")


def cmd_list_blocks(args):
    day = args.date or db.current_day()
    plans = db.get_plans(day)
    if not plans:
        print(f"No plan for {day}.")
        return
    print(f"Schedule — {day}\n")
    for row in plans:
        print(f"  [{row['id']}]  {row['start_time']}–{row['end_time']}  {row['title']}")


def cmd_list_logs(args):
    if args.all:
        with db.get_conn() as conn:
            rows = conn.execute(
                "SELECT day, timestamp, message FROM logs ORDER BY timestamp"
            ).fetchall()
        if not rows:
            print("No logs yet.")
            return
        current = None
        for row in rows:
            if row["day"] != current:
                current = row["day"]
                print(f"\n— {current} —")
            ts = row["timestamp"][11:16]
            print(f"  {ts}  {row['message']}")
    else:
        day = args.date or db.current_day()
        rows = db.get_logs(day)
        if not rows:
            print(f"No logs for {day}.")
            return
        print(f"Logs — {day}\n")
        for row in rows:
            ts = row["timestamp"][11:16]
            print(f"  {ts}  {row['message']}")


def cmd_edit_logs(args):
    import os
    import tempfile

    day = args.date or db.current_day()
    rows = db.get_logs(day)

    lines = [f"# Logs — {day}\n\n"]
    for row in rows:
        ts = row["timestamp"][11:16]
        lines.append(f"{ts}  {row['message']}\n")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.writelines(lines)
        path = f.name

    os.system(f"${{EDITOR:-vim}} {path}")

    with open(path) as f:
        edited = f.readlines()
    os.unlink(path)

    new_entries = []
    for line in edited:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        time_str, message = parts
        try:
            dt = datetime.strptime(f"{day}T{time_str}", "%Y-%m-%dT%H:%M")
        except ValueError:
            print(f"Skipping unparseable line: {line}")
            continue
        new_entries.append((dt.strftime("%Y-%m-%dT%H:%M:%S"), message, day))

    with db.get_conn() as conn:
        conn.execute("DELETE FROM logs WHERE day = ?", (day,))
        conn.executemany("INSERT INTO logs (timestamp, message, day) VALUES (?, ?, ?)", new_entries)

    print(f"Saved {len(new_entries)} entries for {day}.")


def cmd_rm_block(args):
    if db.remove_plan(args.id):
        print(f"Removed block {args.id}.")
    else:
        print(f"No block with id {args.id}.")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Brain CLI")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("add-block", help="Add a plan block")
    p.add_argument("title")
    p.add_argument("start", help="Start time, e.g. 9am or 09:00")
    p.add_argument("end", help="End time, e.g. 10am or 10:00")
    p.add_argument("--date", help="YYYY-MM-DD, defaults to today")

    p = sub.add_parser("list-blocks", help="List plan blocks")
    p.add_argument("--date", help="YYYY-MM-DD, defaults to today")

    p = sub.add_parser("rm-block", help="Remove a plan block by id")
    p.add_argument("id", type=int)

    p = sub.add_parser("list-logs", help="List log entries")
    p.add_argument("--date", help="YYYY-MM-DD, defaults to today")
    p.add_argument("--all", action="store_true", help="Show all logs across all days")

    p = sub.add_parser("edit-logs", help="Edit a day's logs in $EDITOR")
    p.add_argument("--date", help="YYYY-MM-DD, defaults to today")

    args = parser.parse_args()
    if args.command == "add-block":
        cmd_add_block(args)
    elif args.command == "list-blocks":
        cmd_list_blocks(args)
    elif args.command == "list-logs":
        cmd_list_logs(args)
    elif args.command == "rm-block":
        cmd_rm_block(args)
    elif args.command == "edit-logs":
        cmd_edit_logs(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
