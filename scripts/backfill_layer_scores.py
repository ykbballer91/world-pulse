#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DAYS = 30


def parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError("date must use YYYY-MM-DD format") from exc


def date_range(start_date, end_date):
    day = start_date
    while day <= end_date:
        yield day
        day += timedelta(days=1)


def resolve_date_range(args):
    end_date = args.end_date or datetime.now(timezone.utc).date()
    start_date = args.start_date or (end_date - timedelta(days=args.days - 1))
    if start_date > end_date:
        raise ValueError("--start-date must be before or equal to --end-date")
    return start_date, end_date


def script_path(name):
    return os.path.join(ROOT_DIR, "scripts", name)


def run_score_for_date(target_date, database_url):
    command = [
        sys.executable,
        script_path("calculate_weirdness_score.py"),
        "--date",
        target_date.isoformat(),
        "--database-url",
        database_url,
    ]
    child_env = os.environ.copy()
    started = time.monotonic()
    result = subprocess.run(
        command,
        cwd=ROOT_DIR,
        env=child_env,
        check=False,
        capture_output=True,
        text=True,
    )
    elapsed = time.monotonic() - started
    return result, elapsed


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Backfill internal layer score fields by date.")
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS, help="Lookback days.")
    parser.add_argument("--start-date", type=parse_date, default=None, help="Start date YYYY-MM-DD.")
    parser.add_argument("--end-date", type=parse_date, default=None, help="End date YYYY-MM-DD.")
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

    try:
        start_date, end_date = resolve_date_range(args)
    except Exception as exc:
        print(f"Layer score backfill failed: {exc}", file=sys.stderr)
        return 2

    seen = 0
    succeeded = 0
    errors = 0
    failed_dates = []

    for target_date in date_range(start_date, end_date):
        seen += 1
        result, elapsed = run_score_for_date(target_date, args.database_url)
        if result.returncode == 0:
            succeeded += 1
            status = "success"
        else:
            errors += 1
            failed_dates.append(target_date.isoformat())
            status = "failed"
        print(
            "Layer score backfill step: "
            f"date={target_date.isoformat()} "
            f"status={status} "
            f"elapsed_seconds={elapsed:.2f}"
        )
        if result.stdout.strip():
            print(result.stdout.strip())
        if result.stderr.strip():
            print(result.stderr.strip(), file=sys.stderr)

    print(
        "Layer score backfill completed: "
        f"start_date={start_date.isoformat()} "
        f"end_date={end_date.isoformat()} "
        f"seen={seen} "
        f"succeeded={succeeded} "
        f"errors={errors}"
    )
    if failed_dates:
        print("Layer score backfill failed_dates: " + ", ".join(failed_dates))
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
