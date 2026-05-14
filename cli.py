#!/usr/bin/env python3
import argparse
import sys
from datetime import datetime, timedelta

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

    if args.all:
        with db.get_conn() as conn:
            all_rows = conn.execute(
                "SELECT day, timestamp, message FROM logs ORDER BY timestamp"
            ).fetchall()

        today = db.now_mdt().date()
        sunday = today - timedelta(days=(today.weekday() + 1) % 7)
        week_days = {(sunday + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)}
        existing_days = {r["day"] for r in all_rows}
        days = sorted(week_days | existing_days)

        entries = {}
        for row in all_rows:
            entries.setdefault(row["day"], []).append(row)

        lines = []
        for d in days:
            lines.append(f"# {d}\n\n")
            for row in entries.get(d, []):
                lines.append(f"{row['timestamp'][11:16]}  {row['message']}\n")
            lines.append("\n")
    else:
        day = args.date or db.current_day()
        rows = db.get_logs(day)
        lines = [f"# {day}\n\n"]
        for row in rows:
            lines.append(f"{row['timestamp'][11:16]}  {row['message']}\n")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.writelines(lines)
        path = f.name

    os.system(f"${{EDITOR:-vim}} {path}")

    with open(path) as f:
        edited = f.readlines()
    os.unlink(path)

    # Parse edited file — day headers set context for subsequent entries
    entries_by_day = {}
    current_day = None
    for line in edited:
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            current_day = line.lstrip("#").strip()
            entries_by_day.setdefault(current_day, [])
            continue
        if current_day is None:
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        time_str, message = parts
        try:
            dt = datetime.strptime(f"{current_day}T{time_str}", "%Y-%m-%dT%H:%M")
        except ValueError:
            print(f"Skipping: {line}")
            continue
        entries_by_day[current_day].append((dt.strftime("%Y-%m-%dT%H:%M:%S"), message, current_day))

    with db.get_conn() as conn:
        for d, entries in entries_by_day.items():
            conn.execute("DELETE FROM logs WHERE day = ?", (d,))
            conn.executemany("INSERT INTO logs (timestamp, message, day) VALUES (?, ?, ?)", entries)

    total = sum(len(e) for e in entries_by_day.values())
    print(f"Saved {total} entries across {len(entries_by_day)} day(s).")


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

    p = sub.add_parser("edit-logs", help="Edit logs in $EDITOR")
    p.add_argument("--date", help="YYYY-MM-DD, defaults to today")
    p.add_argument("--all", action="store_true", help="Edit all days")

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
