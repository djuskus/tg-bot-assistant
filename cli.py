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

    args = parser.parse_args()
    if args.command == "add-block":
        cmd_add_block(args)
    elif args.command == "list-blocks":
        cmd_list_blocks(args)
    elif args.command == "rm-block":
        cmd_rm_block(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
