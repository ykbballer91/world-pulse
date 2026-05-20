#!/usr/bin/env python3
import argparse
import os
import sys
from datetime import datetime

import psycopg
from dotenv import load_dotenv


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(ROOT_DIR, "public", "share")
PAYLOAD_COLUMNS = ["page_payload", "display_payload", "payload", "metadata"]
MAX_POST_CHARS = 280


def parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--date must use YYYY-MM-DD format") from exc


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


def top_contributor(top_cards):
    contributors = [
        card for card in top_cards if card.get("signal_status") == "score_contributor"
    ]
    if contributors:
        return contributors[0]
    return top_cards[0] if top_cards else None


def summary_line_for_score(score):
    if score <= 20:
        return "Observed public signals were near or below the recent baseline."
    if score <= 50:
        return "Observed public signals were moderately above the recent baseline."
    if score <= 80:
        return "Observed public signals were clearly above the recent baseline."
    return "Observed public signals were unusually elevated relative to the recent baseline."


def build_post_text(display_date, page_payload, url=None):
    score = int(page_payload.get("weirdness_score", 0))
    card = top_contributor(page_payload.get("top_cards", []))
    top_signal = card.get("title") if card else "No top signal available"

    lines = [
        f"World Pulse | Data date: {display_date.isoformat()}",
        f"Latest Weirdness Score: {score}",
        f"Top signal: {top_signal}",
        summary_line_for_score(score),
        "Not a forecast, alert, or recommendation.",
    ]
    if url:
        lines.append(url)
    lines.append("#WorldPulse")
    post_text = "\n".join(lines)

    if len(post_text) > MAX_POST_CHARS:
        raise ValueError(f"generated post is {len(post_text)} characters, above {MAX_POST_CHARS}")
    return post_text


def save_post_text(display_date, post_text):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    dated_path = os.path.join(OUTPUT_DIR, f"world-pulse-{display_date.isoformat()}.txt")
    latest_path = os.path.join(OUTPUT_DIR, "world-pulse-latest.txt")
    for path in [dated_path, latest_path]:
        with open(path, "w", encoding="utf-8") as file:
            file.write(post_text)
            file.write("\n")
    return dated_path, latest_path


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Generate World Pulse X post text.")
    parser.add_argument(
        "--date",
        type=parse_date,
        default=None,
        help="Display date in YYYY-MM-DD format. Defaults to latest display_log date.",
    )
    parser.add_argument(
        "--url",
        default=None,
        help="Optional URL to append to the post text.",
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
        post_text = build_post_text(display_date, page_payload, url=args.url)
        dated_path, latest_path = save_post_text(display_date, post_text)
    except Exception as exc:
        print(f"X post text generation failed: {exc}", file=sys.stderr)
        return 1

    print(
        "Generated X post text: "
        f"display_date={display_date.isoformat()} "
        f"characters={len(post_text)} "
        f"output={os.path.relpath(dated_path, ROOT_DIR)} "
        f"latest={os.path.relpath(latest_path, ROOT_DIR)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
