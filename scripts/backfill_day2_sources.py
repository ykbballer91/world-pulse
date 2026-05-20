#!/usr/bin/env python3
import argparse
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USGS_SCRIPT = os.path.join(ROOT_DIR, "scripts", "ingest_usgs_earthquakes.py")
WIKIPEDIA_SCRIPT = os.path.join(ROOT_DIR, "scripts", "ingest_wikipedia_pageviews.py")


def run_command(args):
    return subprocess.run(
        args,
        cwd=ROOT_DIR,
        check=False,
        capture_output=True,
        text=True,
    )


def parse_int(pattern, text, default=0):
    match = re.search(pattern, text)
    if match is None:
        return default
    return int(match.group(1))


def default_wikipedia_start_date():
    return datetime.now(timezone.utc).date() - timedelta(days=2)


def run_usgs_backfill(days, min_magnitude, database_url):
    hours = days * 24
    target_window = f"last_{days}_days"
    result = run_command(
        [
            sys.executable,
            USGS_SCRIPT,
            "--hours",
            str(hours),
            "--min-magnitude",
            str(min_magnitude),
            "--database-url",
            database_url,
        ]
    )
    output = f"{result.stdout}\n{result.stderr}"
    inserted = parse_int(r"inserted=(\d+)", output)
    seen = parse_int(r"seen=(\d+)", output)
    skipped_below = parse_int(r"skipped_below_min_magnitude=(\d+)", output)
    skipped_duplicates = max(seen - skipped_below - inserted, 0)
    errors = 0 if result.returncode == 0 else 1

    print(
        "Day 2 backfill: "
        "source=usgs "
        f"target_window={target_window} "
        f"inserted={inserted} "
        f"skipped_duplicates={skipped_duplicates} "
        f"errors={errors}"
    )
    if result.returncode != 0:
        print(output.strip(), file=sys.stderr)
    return inserted, skipped_duplicates, errors


def run_wikipedia_for_date(target_date, database_url):
    date_text = target_date.isoformat()
    result = run_command(
        [
            sys.executable,
            WIKIPEDIA_SCRIPT,
            "--date",
            date_text,
            "--database-url",
            database_url,
        ]
    )
    output = f"{result.stdout}\n{result.stderr}"
    inserted = parse_int(r"inserted=(\d+)", output)
    skipped_duplicates = parse_int(r"skipped_duplicates=(\d+)", output)
    errors = 0 if result.returncode == 0 else 1

    print(
        "Day 2 backfill: "
        "source=wikipedia "
        f"target_date={date_text} "
        f"inserted={inserted} "
        f"skipped_duplicates={skipped_duplicates} "
        f"errors={errors}"
    )
    if result.returncode != 0:
        print(output.strip(), file=sys.stderr)
    return inserted, skipped_duplicates, errors


def run_wikipedia_backfill(days, database_url):
    inserted = 0
    skipped_duplicates = 0
    errors = 0
    start_date = default_wikipedia_start_date()

    for offset in range(days):
        target_date = start_date - timedelta(days=offset)
        day_inserted, day_skipped, day_errors = run_wikipedia_for_date(target_date, database_url)
        inserted += day_inserted
        skipped_duplicates += day_skipped
        errors += day_errors

    return inserted, skipped_duplicates, errors


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Backfill Day 2 World Pulse sources.")
    parser.add_argument(
        "--source",
        choices=["usgs", "wikipedia", "all"],
        default="all",
        help="Source to backfill.",
    )
    parser.add_argument("--days", type=int, default=7, help="Number of days to backfill.")
    parser.add_argument(
        "--min-magnitude",
        type=float,
        default=4.0,
        help="Minimum USGS earthquake magnitude.",
    )
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL"),
        help="PostgreSQL connection URL. Defaults to DATABASE_URL.",
    )
    args = parser.parse_args()

    if args.days <= 0:
        print("--days must be greater than zero.", file=sys.stderr)
        return 2

    if not args.database_url:
        print("DATABASE_URL is required.", file=sys.stderr)
        return 2

    os.environ["DATABASE_URL"] = args.database_url

    total_inserted = 0
    total_skipped_duplicates = 0
    total_errors = 0

    if args.source in {"usgs", "all"}:
        inserted, skipped_duplicates, errors = run_usgs_backfill(
            args.days,
            args.min_magnitude,
            args.database_url,
        )
        total_inserted += inserted
        total_skipped_duplicates += skipped_duplicates
        total_errors += errors

    if args.source in {"wikipedia", "all"}:
        inserted, skipped_duplicates, errors = run_wikipedia_backfill(args.days, args.database_url)
        total_inserted += inserted
        total_skipped_duplicates += skipped_duplicates
        total_errors += errors

    print(
        "Day 2 backfill completed: "
        f"source={args.source} "
        f"days={args.days} "
        f"inserted={total_inserted} "
        f"skipped_duplicates={total_skipped_duplicates} "
        f"errors={total_errors}"
    )
    return 1 if total_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
