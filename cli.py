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


def main():
    parser = argparse.ArgumentParser(description="Brain CLI")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("add-block", help="Add a plan block")
    p.add_argument("title")
    p.add_argument("start", help="Start time, e.g. 9am or 09:00")
    p.add_argument("end", help="End time, e.g. 10am or 10:00")
    p.add_argument("--date", help="YYYY-MM-DD, defaults to today")

    args = parser.parse_args()
    if args.command == "add-block":
        cmd_add_block(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
