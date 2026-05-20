#!/usr/bin/env python3
import argparse
import os
import sys
from datetime import datetime, timedelta, timezone

import psycopg
from dotenv import load_dotenv
from psycopg.types.json import Jsonb


PAYLOAD_COLUMNS = [
    "page_payload",
    "display_payload",
    "payload",
    "metadata",
]
CURRENT_SCORE_VERSION = "weirdness_v0_2"
EXCLUDED_TOP_SIGNAL_EVENT_TYPES = {
    "wikipedia_attention_snapshot",
}
QUIET_SIGNAL_CATEGORIES = {
    "geophysical",
    "space_weather",
    "internet",
}


def parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--date must use YYYY-MM-DD format") from exc


def isoformat_z(value):
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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


def latest_score_date(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT score_date
            FROM weirdness_scores
            ORDER BY
              CASE WHEN score_version = %s THEN 0 ELSE 1 END,
              score_date DESC
            LIMIT 1
            """,
            (CURRENT_SCORE_VERSION,),
        )
        row = cur.fetchone()
        if row is None:
            raise ValueError("no weirdness_scores rows were found")
        return row[0]


def fetch_weirdness_score(conn, display_date):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT score_date, score_value, score_version, explanation_payload
            FROM weirdness_scores
            WHERE score_date = %s
            ORDER BY
              CASE WHEN score_version = %s THEN 0 ELSE 1 END,
              calculated_at DESC
            LIMIT 1
            """,
            (display_date, CURRENT_SCORE_VERSION),
        )
        row = cur.fetchone()
        if row is None:
            raise ValueError(f"weirdness score not found for date: {display_date.isoformat()}")
        return row


def utc_day_start(value):
    return datetime(value.year, value.month, value.day, tzinfo=timezone.utc)


def fetch_quiet_signal(conn, display_date):
    window_start = utc_day_start(display_date) - timedelta(hours=48)
    data_end = utc_day_start(display_date) + timedelta(days=1)
    window_end = data_end - timedelta(hours=6)

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                id,
                event_type,
                category,
                title,
                event_time,
                magnitude_value,
                anomaly_score
            FROM normalized_events
            WHERE event_time >= %s
              AND event_time <= %s
              AND event_time IS NOT NULL
              AND anomaly_score > 1.0
              AND event_type <> ALL(%s::text[])
              AND category = ANY(%s::text[])
            ORDER BY anomaly_score DESC, event_time DESC
            LIMIT 1
            """,
            (
                window_start,
                window_end,
                list(EXCLUDED_TOP_SIGNAL_EVENT_TYPES),
                list(QUIET_SIGNAL_CATEGORIES),
            ),
        )
        row = cur.fetchone()

    if row is None:
        return {
            "available": False,
            "note": "No quiet signal available for this data date.",
        }

    event_time = row[4]
    if event_time.tzinfo is None:
        event_time = event_time.replace(tzinfo=timezone.utc)
    event_time = event_time.astimezone(timezone.utc)
    hours_ago = round((data_end - event_time).total_seconds() / 3600, 1)
    hours_label = round(hours_ago)

    return {
        "available": True,
        "id": str(row[0]),
        "title": row[3],
        "event_type": row[1],
        "category": row[2],
        "event_time": isoformat_z(event_time),
        "hours_ago_from_data_end": hours_ago,
        "anomaly_score": float(row[6]),
        "magnitude_value": float(row[5]) if row[5] is not None else None,
        "summary": (
            f"{row[3]}, observed about {hours_label} hours before the end of the data date."
        ),
        "note": "This signal sits above the recent baseline within the current data window.",
        "safety_note": "Not a forecast, alert, or recommendation.",
    }


def summary_line_for_score(score_value):
    if score_value <= 20:
        return "Observed public signals were near or below the recent baseline."
    if score_value <= 50:
        return "Observed public signals were moderately above the recent baseline."
    if score_value <= 80:
        return "Observed public signals were clearly above the recent baseline."
    return "Observed public signals were unusually elevated relative to the recent baseline."


def ordinal(value):
    number = int(round(value))
    if 10 <= number % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
    return f"{number}{suffix}"


def percentile_line(score_value, explanation_payload):
    percentile = explanation_payload.get("percentile_rank", score_value)
    window_days = int(explanation_payload.get("window_days", 30))
    return (
        f"This data date is in the {ordinal(percentile)} percentile "
        f"of the last {window_days} observed days."
    )


def build_top_cards(top_events):
    cards = []
    weights = [20, 10, 5]
    display_events = [
        event
        for event in top_events
        if event.get("event_type") not in EXCLUDED_TOP_SIGNAL_EVENT_TYPES
    ]
    for index, event in enumerate(display_events):
        anomaly_score = event.get("anomaly_score")
        effective_anomaly = max(float(anomaly_score), 0) if anomaly_score is not None else 0
        score_contribution = weights[index] * effective_anomaly if index < len(weights) else 0
        signal_status = "score_contributor" if effective_anomaly > 0 else "context_only"
        display_note = (
            "Above the recent baseline."
            if signal_status == "score_contributor"
            else "Observed signal, but not above the recent baseline."
        )
        cards.append(
            {
                "title": event.get("title"),
                "event_type": event.get("event_type"),
                "category": event.get("category"),
                "event_time": event.get("event_time"),
                "magnitude_value": event.get("magnitude_value"),
                "anomaly_score": anomaly_score,
                "effective_anomaly": effective_anomaly,
                "score_contribution": score_contribution,
                "signal_status": signal_status,
                "display_note": display_note,
                "source_note": "Public observation data",
            }
        )
    return cards


def build_page_payload(score_row, quiet_signal):
    score_date, score_value, score_version, explanation_payload = score_row
    top_events = explanation_payload.get("top_events", [])
    now = datetime.now(timezone.utc)
    data_date = explanation_payload.get("data_date", score_date.isoformat())
    line = (
        percentile_line(score_value, explanation_payload)
        if score_version == CURRENT_SCORE_VERSION
        else summary_line_for_score(score_value)
    )
    top_cards = build_top_cards(top_events)

    return {
        "date": score_date.isoformat(),
        "data_date": data_date,
        "weirdness_score": score_value,
        "score_version": score_version,
        "headline": "Latest Weirdness Score",
        "percentile_line": line,
        "summary_lines": [
            line,
            "The score is based on public earthquake and Wikipedia attention data.",
            "This is not a forecast, alert, or recommendation.",
        ],
        "top_cards": top_cards,
        "quiet_signal": quiet_signal,
        "top_signal_note": (
            None
            if top_cards
            else "No individual top signal available for this data date."
        ),
        "principles": {
            "no_prediction": True,
            "no_fear_amplification": True,
            "no_trading_or_investment_advice": True,
        },
        "updated_at": isoformat_z(now),
    }


def choose_payload_column(columns):
    for column in PAYLOAD_COLUMNS:
        if column in columns:
            return column
    return None


def existing_display_exists(conn, columns, display_date):
    if "display_date" not in columns:
        return False

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT 1
            FROM display_log
            WHERE display_date = %s
            LIMIT 1
            """,
            (display_date,),
        )
        return cur.fetchone() is not None


def assign_if_column(values, columns, column, value):
    if column in columns:
        values[column] = value


def build_display_values(columns, display_date, page_payload):
    values = {}
    payload_column = choose_payload_column(columns)
    now = datetime.now(timezone.utc)

    assign_if_column(values, columns, "display_date", display_date)
    assign_if_column(values, columns, "score_date", display_date)
    assign_if_column(values, columns, "weirdness_score", page_payload["weirdness_score"])
    assign_if_column(values, columns, "score_value", page_payload["weirdness_score"])
    assign_if_column(values, columns, "score_version", page_payload["score_version"])
    assign_if_column(values, columns, "quiet_signal", Jsonb(page_payload["quiet_signal"]))
    assign_if_column(values, columns, "generated_at", now)
    assign_if_column(values, columns, "created_at", now)
    assign_if_column(values, columns, "updated_at", now)

    if payload_column is not None:
        values[payload_column] = Jsonb(page_payload)

    return values


def save_display_payload(conn, columns, display_date, page_payload):
    if "display_date" not in columns:
        raise ValueError("display_log must include display_date")

    values = build_display_values(columns, display_date, page_payload)
    exists = existing_display_exists(conn, columns, display_date)

    with conn.cursor() as cur:
        if exists:
            update_values = {
                column: value for column, value in values.items() if column != "created_at"
            }
            assignments = ", ".join(f"{column} = %s" for column in update_values)
            if not assignments:
                return "skipped"
            cur.execute(
                f"""
                UPDATE display_log
                SET {assignments}
                WHERE display_date = %s
                """,
                [*update_values.values(), display_date],
            )
            return "updated"

        insert_columns = list(values)
        placeholders = ", ".join(["%s"] * len(insert_columns))
        column_sql = ", ".join(insert_columns)
        cur.execute(
            f"""
            INSERT INTO display_log ({column_sql})
            VALUES ({placeholders})
            """,
            [values[column] for column in insert_columns],
        )
        return "inserted"


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Generate World Pulse display payload.")
    parser.add_argument(
        "--date",
        type=parse_date,
        default=None,
        help="Display date in YYYY-MM-DD format. Defaults to latest weirdness score date.",
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

    inserted = 0
    updated = 0
    errors = 0

    conn = None
    try:
        with psycopg.connect(args.database_url) as conn:
            columns = table_columns(conn, "display_log")
            if not columns:
                print("display_log table was not found.", file=sys.stderr)
                return 1

            display_date = args.date or latest_score_date(conn)
            score_row = fetch_weirdness_score(conn, display_date)
            quiet_signal = fetch_quiet_signal(conn, display_date)
            page_payload = build_page_payload(score_row, quiet_signal)
            status = save_display_payload(conn, columns, display_date, page_payload)
            if status == "inserted":
                inserted = 1
            elif status == "updated":
                updated = 1
            conn.commit()

    except Exception as exc:
        if conn is not None:
            conn.rollback()
        errors = 1
        display_date_text = args.date.isoformat() if args.date else "latest_score_date"
        print(f"Display payload generation failed: display_date={display_date_text} error={exc}", file=sys.stderr)
        return 1

    print(
        "Display payload generation completed: "
        f"display_date={display_date.isoformat()} "
        f"weirdness_score={page_payload['weirdness_score']} "
        f"top_cards={len(page_payload['top_cards'])} "
        f"inserted={inserted} "
        f"updated={updated} "
        f"errors={errors}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
