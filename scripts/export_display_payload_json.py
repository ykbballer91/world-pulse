#!/usr/bin/env python3
import argparse
import json
import os
import sys
from datetime import date, datetime

import psycopg
from dotenv import load_dotenv


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(ROOT_DIR, "public", "display", "latest.json")
PAYLOAD_COLUMNS = ["page_payload", "display_payload", "payload", "metadata"]


def parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--date must use YYYY-MM-DD format") from exc


def json_default(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


def table_columns(conn, table_name):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
            """,
            (table_name,),
        )
        return {row[0] for row in cur.fetchall()}


def choose_payload_column(columns):
    for column in PAYLOAD_COLUMNS:
        if column in columns:
            return column
    raise ValueError("display_log must include a page payload JSON column")


def latest_display_date(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT display_date
            FROM display_log
            ORDER BY display_date DESC
            LIMIT 1
            """
        )
        row = cur.fetchone()
        if row is None:
            raise ValueError("no display_log rows were found")
        return row[0]


def fetch_display_payload(conn, display_date):
    columns = table_columns(conn, "display_log")
    if not columns:
        raise ValueError("display_log table was not found")
    if "display_date" not in columns:
        raise ValueError("display_log must include display_date")

    payload_column = choose_payload_column(columns)
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT display_date, {payload_column}
            FROM display_log
            WHERE display_date = %s
            LIMIT 1
            """,
            (display_date,),
        )
        row = cur.fetchone()
        if row is None:
            raise ValueError(f"display payload not found for date: {display_date.isoformat()}")
        return row


def write_latest_json(display_date, page_payload):
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    payload = {
        "display_date": display_date.isoformat(),
        "page_payload": page_payload,
    }
    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2, default=json_default)
        file.write("\n")


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Export World Pulse display payload JSON.")
    parser.add_argument(
        "--date",
        type=parse_date,
        default=None,
        help="Display date in YYYY-MM-DD format. Defaults to latest display_log date.",
    )
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL"),
        help="PostgreSQL connection URL. Defaults to DATABASE_URL.",
    )
    args = parser.parse_args()

    if not args.database_url:
        print("DATABASE_URL is required.", file=sys.stderr)
        return 2

    try:
        with psycopg.connect(args.database_url) as conn:
            display_date = args.date or latest_display_date(conn)
            display_date, page_payload = fetch_display_payload(conn, display_date)
            write_latest_json(display_date, page_payload)
    except Exception as exc:
        print(f"Display payload export failed: {exc}", file=sys.stderr)
        return 1

    print(
        "Exported display payload: "
        f"display_date={display_date.isoformat()} "
        "output=public/display/latest.json"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
