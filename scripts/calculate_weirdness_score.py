#!/usr/bin/env python3
import argparse
import os
import sys
from datetime import datetime, timedelta, timezone

import psycopg
from dotenv import load_dotenv
from psycopg.types.json import Jsonb


VERSION_KEY = "weirdness_v0_2"
FORMULA_TEXT = (
    "Daily raw score is computed from the top positive anomaly scores for each observed day. "
    "The displayed Weirdness Score is the percentile rank of the selected data date's raw score "
    "within the recent baseline window."
)
TOP_WEIGHTS = [20, 10, 5]
DEFAULT_WINDOW_DAYS = 30
VERSION_PARAMETERS = {
    "window_days": DEFAULT_WINDOW_DAYS,
    "top_weights": TOP_WEIGHTS,
    "percentile_method": "midrank",
    "negative_anomaly_policy": "effective_anomaly = max(anomaly_score, 0)",
    "score_range": [0, 100],
}
EXCLUDED_TOP_SIGNAL_EVENT_TYPES = {
    "wikipedia_attention_snapshot",
}

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
              AND anomaly_score IS NOT NULL
            ORDER BY event_time DESC
            LIMIT 1
            """
        )
        row = cur.fetchone()
        if row is None:
            raise ValueError("no normalized_events with event_time were found")
        return row[0]


def ensure_score_version(conn, columns, window_days):
    required = {"version_key"}
    if not required.issubset(columns):
        raise ValueError("score_versions must include version_key")

    parameters = dict(VERSION_PARAMETERS)
    parameters["window_days"] = window_days

    values = {"version_key": VERSION_KEY}
    if "formula_text" in columns:
        values["formula_text"] = FORMULA_TEXT
    elif "formula" in columns:
        values["formula"] = FORMULA_TEXT
    if "parameters" in columns:
        values["parameters"] = Jsonb(parameters)
    if "updated_at" in columns:
        values["updated_at"] = datetime.now(timezone.utc)

    with conn.cursor() as cur:
        insert_values = dict(values)
        if "created_at" in columns:
            insert_values["created_at"] = datetime.now(timezone.utc)

        insert_columns = list(insert_values)
        placeholders = ", ".join(["%s"] * len(insert_columns))
        column_sql = ", ".join(insert_columns)
        update_columns = [column for column in values if column != "version_key"]
        update_sql = ", ".join(f"{column} = EXCLUDED.{column}" for column in update_columns)
        conflict_sql = f"DO UPDATE SET {update_sql}" if update_sql else "DO NOTHING"
        cur.execute(
            f"""
            INSERT INTO score_versions ({column_sql})
            VALUES ({placeholders})
            ON CONFLICT (version_key) {conflict_sql}
            """,
            [insert_values[column] for column in insert_columns],
        )


def fetch_events_for_window(conn, window_start_date, window_end_date):
    window_start = datetime(
        window_start_date.year,
        window_start_date.month,
        window_start_date.day,
        tzinfo=timezone.utc,
    )
    window_end = datetime(
        window_end_date.year,
        window_end_date.month,
        window_end_date.day,
        tzinfo=timezone.utc,
    ) + timedelta(days=1)
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
            ORDER BY event_time ASC
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


def sort_events_for_score(events):
    return sorted(
        events,
        key=lambda event: (
            event["effective_anomaly"],
            float(event["anomaly_score"]),
            event["event_time"],
        ),
        reverse=True,
    )


def calculate_daily_raw_score(events):
    scored_events = sort_events_for_score(events)
    top_events = scored_events[:3]
    raw_score = sum(
        weight * event["effective_anomaly"] for weight, event in zip(TOP_WEIGHTS, top_events)
    )
    return raw_score, top_events, scored_events


def display_top_events(events):
    return [
        event
        for event in sort_events_for_score(events)
        if event["event_type"] not in EXCLUDED_TOP_SIGNAL_EVENT_TYPES
    ][:3]


def calculate_window_scores(events, target_date, window_days):
    window_start_date = target_date - timedelta(days=window_days - 1)
    events_by_date = {}
    for event in events:
        events_by_date.setdefault(event["event_time"].date(), []).append(event)

    daily_raw_scores = []
    target_scoring_top_events = []
    target_display_top_events = []
    target_scored_events = []
    for offset in range(window_days):
        day = window_start_date + timedelta(days=offset)
        day_events = events_by_date.get(day, [])
        raw_score, top_events, scored_events = calculate_daily_raw_score(day_events)
        if day == target_date:
            target_scoring_top_events = top_events
            target_display_top_events = display_top_events(day_events)
            target_scored_events = scored_events
        daily_raw_scores.append(
            {
                "date": day.isoformat(),
                "raw_score": raw_score,
                "event_count": len(day_events),
            }
        )

    target_raw_score = next(
        item["raw_score"] for item in daily_raw_scores if item["date"] == target_date.isoformat()
    )
    raw_values = [item["raw_score"] for item in daily_raw_scores]
    less_count = sum(1 for value in raw_values if value < target_raw_score)
    equal_count = sum(1 for value in raw_values if value == target_raw_score)
    sample_count = len(raw_values)
    percentile_rank = 100 * (less_count + 0.5 * equal_count) / sample_count
    score_value = round(max(0, min(percentile_rank, 100)))

    return {
        "score_value": score_value,
        "raw_score": target_raw_score,
        "percentile_rank": percentile_rank,
        "history_sample_count": sample_count,
        "less_count": less_count,
        "equal_count": equal_count,
        "daily_raw_scores": daily_raw_scores,
        "top_events": target_display_top_events,
        "scoring_top_events": target_scoring_top_events,
        "scored_events": target_scored_events,
        "positive_events": [
            event for event in events_by_date.get(target_date, []) if event["effective_anomaly"] > 0
        ],
        "window_start": window_start_date,
        "window_end": target_date,
    }


def json_ready_event(event):
    return {
        "id": str(event["id"]),
        "event_type": event["event_type"],
        "category": event["category"],
        "title": event["title"],
        "event_time": isoformat_z(event["event_time"]),
        "magnitude_value": float(event["magnitude_value"]) if event["magnitude_value"] is not None else None,
        "anomaly_score": float(event["anomaly_score"]),
        "effective_anomaly": event["effective_anomaly"],
    }


def build_component_scores(score_result, window_days):
    return {
        "raw_score": score_result["raw_score"],
        "percentile_rank": score_result["percentile_rank"],
        "history_sample_count": score_result["history_sample_count"],
        "window_days": window_days,
        "target_raw_score": score_result["raw_score"],
        "less_count": score_result["less_count"],
        "equal_count": score_result["equal_count"],
        "top_weights": TOP_WEIGHTS,
        "daily_raw_scores": score_result["daily_raw_scores"],
        "scoring_top_events": [
            json_ready_event(event) for event in score_result["scoring_top_events"]
        ],
        "excluded_top_signal_event_types": sorted(EXCLUDED_TOP_SIGNAL_EVENT_TYPES),
        "display_top_event_count": len(score_result["top_events"]),
        "scoring_top_event_count": len(score_result["scoring_top_events"]),
    }


def build_explanation_payload(score_date, score_result, window_days):
    return {
        "score_version": VERSION_KEY,
        "data_date": score_date.isoformat(),
        "score_date": score_date.isoformat(),
        "raw_score": score_result["raw_score"],
        "percentile_rank": score_result["percentile_rank"],
        "history_sample_count": score_result["history_sample_count"],
        "window_days": window_days,
        "low_sample_count": score_result["history_sample_count"] < 3,
        "formula": FORMULA_TEXT,
        "score_value": score_result["score_value"],
        "top_events": [json_ready_event(event) for event in score_result["top_events"]],
        "scoring_top_events": [
            json_ready_event(event) for event in score_result["scoring_top_events"]
        ],
        "excluded_top_signal_event_types": sorted(EXCLUDED_TOP_SIGNAL_EVENT_TYPES),
        "principles": {
            "no_prediction": True,
            "no_fear_amplification": True,
            "no_trading_or_investment_advice": True,
        },
        "note": (
            "This score summarizes observed public signals for the selected data date. "
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


def build_score_values(columns, score_date, score_result, explanation_payload, component_scores):
    values = {}
    json_column = choose_json_column(columns)
    top_event_ids = [str(event["id"]) for event in score_result["top_events"]]

    assign_if_column(values, columns, "score_date", score_date)
    assign_if_column(values, columns, "score_value", score_result["score_value"])
    assign_if_column(values, columns, "score_version", VERSION_KEY)
    assign_if_column(values, columns, "top_event_ids", top_event_ids)
    assign_if_column(values, columns, "component_scores", Jsonb(component_scores))
    assign_if_column(values, columns, "calculated_at", datetime.now(timezone.utc))
    assign_if_column(values, columns, "created_at", datetime.now(timezone.utc))
    assign_if_column(values, columns, "updated_at", datetime.now(timezone.utc))

    if json_column is not None:
        values[json_column] = Jsonb(explanation_payload)

    return values


def save_weirdness_score(conn, columns, score_date, score_result, explanation_payload, component_scores):
    if not {"score_date", "score_version"}.issubset(columns):
        raise ValueError("weirdness_scores must include score_date and score_version")

    values = build_score_values(columns, score_date, score_result, explanation_payload, component_scores)
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
        "--window-days",
        type=int,
        default=DEFAULT_WINDOW_DAYS,
        help="Percentile baseline window in days.",
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
    if args.window_days <= 0:
        print("--window-days must be greater than zero.", file=sys.stderr)
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

            ensure_score_version(conn, score_version_columns, args.window_days)
            score_date = args.date or latest_observation_date(conn)
            window_start = score_date - timedelta(days=args.window_days - 1)
            candidate_events = fetch_events_for_window(conn, window_start, score_date)
            score_result = calculate_window_scores(candidate_events, score_date, args.window_days)
            explanation_payload = build_explanation_payload(score_date, score_result, args.window_days)
            component_scores = build_component_scores(score_result, args.window_days)
            status = save_weirdness_score(
                conn,
                weirdness_columns,
                score_date,
                score_result,
                explanation_payload,
                component_scores,
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
        f"scored_events={len(score_result['scored_events'])} "
        f"positive_events={len(score_result['positive_events'])} "
        f"top_events={len(score_result['top_events'])} "
        f"scoring_top_events={len(score_result['scoring_top_events'])} "
        f"raw_score={score_result['raw_score']:.4f} "
        f"percentile_rank={score_result['percentile_rank']:.2f} "
        f"score_value={score_result['score_value']} "
        f"inserted={inserted} "
        f"updated={updated} "
        f"errors={errors}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
