#!/usr/bin/env python3
import argparse
import os
import sys
from datetime import datetime, timedelta, timezone

import psycopg
from dotenv import load_dotenv
from psycopg.types.json import Jsonb


VERSION_KEY = "weirdness_v0_1"
FORMULA_TEXT = (
    "raw_score = 20*top1 + 10*top2 + 5*top3, using positive anomaly scores only; "
    "weirdness_score = clamp(round(raw_score), 0, 100)"
)

JSON_COLUMNS = [
    "explanation_payload",
    "payload",
    "metadata",
]


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


def latest_observation_date(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT event_time::date
            FROM normalized_events
            WHERE event_time IS NOT NULL
            ORDER BY event_time DESC
            LIMIT 1
            """
        )
        row = cur.fetchone()
        if row is None:
            raise ValueError("no normalized_events with event_time were found")
        return row[0]


def ensure_score_version(conn, columns):
    required = {"version_key"}
    if not required.issubset(columns):
        raise ValueError("score_versions must include version_key")

    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM score_versions WHERE version_key = %s LIMIT 1",
            (VERSION_KEY,),
        )
        if cur.fetchone() is not None:
            return

        values = {"version_key": VERSION_KEY}
        if "formula_text" in columns:
            values["formula_text"] = FORMULA_TEXT
        elif "formula" in columns:
            values["formula"] = FORMULA_TEXT
        if "created_at" in columns:
            values["created_at"] = datetime.now(timezone.utc)
        if "updated_at" in columns:
            values["updated_at"] = datetime.now(timezone.utc)

        insert_columns = list(values)
        placeholders = ", ".join(["%s"] * len(insert_columns))
        column_sql = ", ".join(insert_columns)
        cur.execute(
            f"""
            INSERT INTO score_versions ({column_sql})
            VALUES ({placeholders})
            """,
            [values[column] for column in insert_columns],
        )


def fetch_candidate_events(conn, score_date):
    window_start = datetime(score_date.year, score_date.month, score_date.day, tzinfo=timezone.utc)
    window_end = window_start + timedelta(days=1)

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
              AND event_time < %s
              AND anomaly_score IS NOT NULL
            ORDER BY anomaly_score DESC
            """,
            (window_start, window_end),
        )
        rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "event_type": row[1],
            "category": row[2],
            "title": row[3],
            "event_time": row[4],
            "magnitude_value": row[5],
            "anomaly_score": row[6],
            "effective_anomaly": max(float(row[6]), 0),
        }
        for row in rows
    ]


def calculate_score(events):
    scored_events = sorted(
        events,
        key=lambda event: (event["effective_anomaly"], float(event["anomaly_score"])),
        reverse=True,
    )
    positive_events = [event for event in events if event["effective_anomaly"] > 0]
    top_events = scored_events[:3]
    weights = [20, 10, 5]
    raw_score = sum(
        weight * event["effective_anomaly"] for weight, event in zip(weights, top_events)
    )
    score_value = round(max(0, min(raw_score, 100)))
    return score_value, top_events, scored_events, positive_events


def json_ready_event(event):
    return {
        "id": str(event["id"]),
        "event_type": event["event_type"],
        "category": event["category"],
        "title": event["title"],
        "event_time": isoformat_z(event["event_time"]),
        "magnitude_value": event["magnitude_value"],
        "anomaly_score": event["anomaly_score"],
        "effective_anomaly": event["effective_anomaly"],
    }


def build_explanation_payload(score_date, score_value, top_events):
    return {
        "score_date": score_date.isoformat(),
        "score_version": VERSION_KEY,
        "formula": FORMULA_TEXT,
        "score_value": score_value,
        "top_events": [json_ready_event(event) for event in top_events],
        "principles": {
            "no_prediction": True,
            "no_fear_amplification": True,
            "no_trading_or_investment_advice": True,
        },
        "note": (
            "This score summarizes observed public signals for the selected date. "
            "It is not a forecast, alert, or recommendation."
        ),
    }


def choose_json_column(columns):
    for column in JSON_COLUMNS:
        if column in columns:
            return column
    return None


def existing_score_exists(conn, columns, score_date):
    if not {"score_date", "score_version"}.issubset(columns):
        return False

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT 1
            FROM weirdness_scores
            WHERE score_date = %s
              AND score_version = %s
            LIMIT 1
            """,
            (score_date, VERSION_KEY),
        )
        return cur.fetchone() is not None


def assign_if_column(values, columns, column, value):
    if column in columns:
        values[column] = value


def build_score_values(columns, score_date, score_value, top_events, explanation_payload):
    values = {}
    json_column = choose_json_column(columns)
    top_event_ids = [str(event["id"]) for event in top_events]
    component_scores = [
        {
            "event_id": str(event["id"]),
            "effective_anomaly": event["effective_anomaly"],
            "weight": weight,
            "weighted_score": weight * event["effective_anomaly"],
        }
        for weight, event in zip([20, 10, 5], top_events)
    ]

    assign_if_column(values, columns, "score_date", score_date)
    assign_if_column(values, columns, "score_value", score_value)
    assign_if_column(values, columns, "score_version", VERSION_KEY)
    assign_if_column(values, columns, "top_event_ids", top_event_ids)
    assign_if_column(values, columns, "component_scores", Jsonb(component_scores))
    assign_if_column(values, columns, "calculated_at", datetime.now(timezone.utc))
    assign_if_column(values, columns, "created_at", datetime.now(timezone.utc))
    assign_if_column(values, columns, "updated_at", datetime.now(timezone.utc))

    if json_column is not None:
        values[json_column] = Jsonb(explanation_payload)

    return values


def save_weirdness_score(conn, columns, score_date, score_value, top_events, explanation_payload):
    if not {"score_date", "score_version"}.issubset(columns):
        raise ValueError("weirdness_scores must include score_date and score_version")

    values = build_score_values(columns, score_date, score_value, top_events, explanation_payload)
    exists = existing_score_exists(conn, columns, score_date)

    with conn.cursor() as cur:
        if exists:
            update_values = {
                column: value for column, value in values.items() if column != "created_at"
            }
            assignments = ", ".join(
                f"{column} = %s::uuid[]" if column == "top_event_ids" else f"{column} = %s"
                for column in update_values
            )
            if not assignments:
                return "skipped"
            cur.execute(
                f"""
                UPDATE weirdness_scores
                SET {assignments}
                WHERE score_date = %s
                  AND score_version = %s
                """,
                [*update_values.values(), score_date, VERSION_KEY],
            )
            return "updated"

        insert_columns = list(values)
        placeholders = ", ".join(
            "%s::uuid[]" if column == "top_event_ids" else "%s"
            for column in insert_columns
        )
        column_sql = ", ".join(insert_columns)
        cur.execute(
            f"""
            INSERT INTO weirdness_scores ({column_sql})
            VALUES ({placeholders})
            """,
            [values[column] for column in insert_columns],
        )
        return "inserted"


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Calculate World Pulse Weirdness Score.")
    parser.add_argument(
        "--date",
        type=parse_date,
        default=None,
        help="Score date in YYYY-MM-DD format. Defaults to the latest observed UTC date.",
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
            score_version_columns = table_columns(conn, "score_versions")
            weirdness_columns = table_columns(conn, "weirdness_scores")
            if not score_version_columns:
                print("score_versions table was not found.", file=sys.stderr)
                return 1
            if not weirdness_columns:
                print("weirdness_scores table was not found.", file=sys.stderr)
                return 1

            ensure_score_version(conn, score_version_columns)
            score_date = args.date or latest_observation_date(conn)
            candidate_events = fetch_candidate_events(conn, score_date)
            score_value, top_events, scored_events, positive_events = calculate_score(candidate_events)
            explanation_payload = build_explanation_payload(score_date, score_value, top_events)
            status = save_weirdness_score(
                conn,
                weirdness_columns,
                score_date,
                score_value,
                top_events,
                explanation_payload,
            )
            if status == "inserted":
                inserted = 1
            elif status == "updated":
                updated = 1
            conn.commit()

    except Exception as exc:
        if conn is not None:
            conn.rollback()
        errors = 1
        score_date_text = args.date.isoformat() if args.date else "latest_observed"
        print(f"Weirdness Score calculation failed: score_date={score_date_text} error={exc}", file=sys.stderr)
        return 1

    print(
        "Weirdness Score calculation completed: "
        f"score_date={score_date.isoformat()} "
        f"candidate_events={len(candidate_events)} "
        f"scored_events={len(scored_events)} "
        f"positive_events={len(positive_events)} "
        f"top_events={len(top_events)} "
        f"score_value={score_value} "
        f"inserted={inserted} "
        f"updated={updated} "
        f"errors={errors}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
