#!/usr/bin/env python3
import argparse
import json
import os
import sys
from datetime import datetime, timezone

import psycopg
from dotenv import load_dotenv
from psycopg.types.json import Jsonb


USGS_SOURCE_NAME = "USGS Earthquake Hazards Program"
WIKIPEDIA_SOURCE_NAME = "Wikipedia Pageviews"

PAYLOAD_COLUMNS = [
    "normalized_payload",
    "payload",
    "event_payload",
    "metadata",
]


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


def get_source_id(conn, source_name):
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM sources WHERE name = %s", (source_name,))
        row = cur.fetchone()
        if row is None:
            raise ValueError(f"source not found: {source_name}")
        return row[0]


def choose_payload_column(columns):
    for column in PAYLOAD_COLUMNS:
        if column in columns:
            return column
    return None


def fetch_baseline(conn, source_id, metric_key):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT sample_count, mean_value, stddev_value
            FROM baseline_distributions
            WHERE source_id = %s
              AND metric_key = %s
            ORDER BY window_end DESC
            LIMIT 1
            """,
            (source_id, metric_key),
        )
        return cur.fetchone()


def anomaly_score(value, baseline):
    if value is None or baseline is None:
        return None

    sample_count, mean_value, stddev_value = baseline
    if sample_count is None or sample_count < 3:
        return None
    if mean_value is None or stddev_value is None or stddev_value == 0:
        return None
    return (float(value) - float(mean_value)) / float(stddev_value)


def article_views(article):
    try:
        return int(article.get("views"))
    except (TypeError, ValueError):
        return 0


def is_excluded_wikipedia_title(article):
    return article.get("article") in {"Main_Page", "Special:Search"}


def existing_event_exists(conn, raw_observation_id, event_type):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT 1
            FROM normalized_events
            WHERE raw_observation_id = %s
              AND event_type = %s
            LIMIT 1
            """,
            (raw_observation_id, event_type),
        )
        return cur.fetchone() is not None


def assign_if_column(values, columns, column, value):
    if column in columns:
        values[column] = value


def build_event_values(columns, event):
    values = {}
    payload_column = choose_payload_column(columns)

    for column in [
        "raw_observation_id",
        "source_id",
        "event_type",
        "category",
        "title",
        "event_time",
        "magnitude_value",
        "location_label",
        "latitude",
        "longitude",
        "anomaly_score",
    ]:
        assign_if_column(values, columns, column, event.get(column))

    if payload_column is not None:
        values[payload_column] = Jsonb(event["normalized_payload"])

    now = datetime.now(timezone.utc)
    assign_if_column(values, columns, "created_at", now)
    assign_if_column(values, columns, "updated_at", now)
    return values


def save_normalized_event(conn, columns, event):
    required = {"raw_observation_id", "event_type"}
    if not required.issubset(columns):
        raise ValueError("normalized_events must include raw_observation_id and event_type")

    values = build_event_values(columns, event)
    exists = existing_event_exists(conn, event["raw_observation_id"], event["event_type"])

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
                UPDATE normalized_events
                SET {assignments}
                WHERE raw_observation_id = %s
                  AND event_type = %s
                """,
                [
                    *update_values.values(),
                    event["raw_observation_id"],
                    event["event_type"],
                ],
            )
            return "updated"

        insert_columns = list(values)
        placeholders = ", ".join(["%s"] * len(insert_columns))
        column_sql = ", ".join(insert_columns)
        cur.execute(
            f"""
            INSERT INTO normalized_events ({column_sql})
            VALUES ({placeholders})
            """,
            [values[column] for column in insert_columns],
        )
        return "inserted"


def fetch_usgs_raw_observations(conn, source_id):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, observed_at, raw_payload
            FROM raw_observations
            WHERE source_id = %s
            ORDER BY observed_at
            """,
            (source_id,),
        )
        return cur.fetchall()


def build_usgs_event(source_id, row, baseline):
    raw_observation_id, observed_at, raw_payload = row
    properties = raw_payload.get("properties", {})
    geometry = raw_payload.get("geometry", {})
    coordinates = geometry.get("coordinates") or []

    magnitude = properties.get("mag")
    try:
        magnitude_value = float(magnitude) if magnitude is not None else None
    except (TypeError, ValueError):
        magnitude_value = None

    place = properties.get("place") or "unknown location"
    longitude = coordinates[0] if len(coordinates) > 0 else None
    latitude = coordinates[1] if len(coordinates) > 1 else None
    depth = coordinates[2] if len(coordinates) > 2 else None

    title_magnitude = magnitude if magnitude is not None else "unknown magnitude"
    return {
        "raw_observation_id": raw_observation_id,
        "source_id": source_id,
        "event_type": "earthquake",
        "category": "geophysical",
        "title": f"M{title_magnitude} earthquake near {place}",
        "event_time": observed_at,
        "magnitude_value": magnitude_value,
        "location_label": place,
        "latitude": latitude,
        "longitude": longitude,
        "anomaly_score": anomaly_score(magnitude_value, baseline),
        "normalized_payload": {
            "usgs_id": raw_payload.get("id"),
            "place": place,
            "mag": magnitude,
            "depth": depth,
            "url": properties.get("url"),
            "event_type": properties.get("type"),
            "time": properties.get("time"),
            "updated": properties.get("updated"),
        },
    }


def fetch_wikipedia_raw_observations(conn, source_id):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, observed_at, raw_payload
            FROM raw_observations
            WHERE source_id = %s
              AND raw_payload->>'dataset' = 'top_pageviews'
            ORDER BY observed_at
            """,
            (source_id,),
        )
        return cur.fetchall()


def build_wikipedia_event(source_id, row, baseline):
    raw_observation_id, observed_at, raw_payload = row
    records = raw_payload.get("records") or []
    date_text = raw_payload.get("date")

    top1000_total = sum(article_views(article) for article in records[:1000])
    top10_total = sum(article_views(article) for article in records[:10])
    filtered_records = [article for article in records if not is_excluded_wikipedia_title(article)]
    top10_excluding_main = sum(article_views(article) for article in filtered_records[:10])

    return {
        "raw_observation_id": raw_observation_id,
        "source_id": source_id,
        "event_type": "wikipedia_attention_snapshot",
        "category": "attention",
        "title": f"Wikipedia attention snapshot for {date_text}",
        "event_time": observed_at,
        "magnitude_value": top1000_total,
        "location_label": None,
        "latitude": None,
        "longitude": None,
        "anomaly_score": anomaly_score(top1000_total, baseline),
        "normalized_payload": {
            "date": date_text,
            "project": raw_payload.get("project"),
            "access": raw_payload.get("access"),
            "top1000_total_views": top1000_total,
            "top10_total_views": top10_total,
            "top10_total_views_excluding_main_page": top10_excluding_main,
            "top_articles": records[:10],
        },
    }


def generate_for_source(conn, columns, source):
    if source == "usgs":
        source_id = get_source_id(conn, USGS_SOURCE_NAME)
        rows = fetch_usgs_raw_observations(conn, source_id)
        baseline = fetch_baseline(conn, source_id, "usgs_daily_max_magnitude")
        events = [build_usgs_event(source_id, row, baseline) for row in rows]
    elif source == "wikipedia":
        source_id = get_source_id(conn, WIKIPEDIA_SOURCE_NAME)
        rows = fetch_wikipedia_raw_observations(conn, source_id)
        baseline = fetch_baseline(conn, source_id, "wikipedia_daily_top1000_total_views")
        events = [build_wikipedia_event(source_id, row, baseline) for row in rows]
    else:
        raise ValueError(f"unsupported source: {source}")

    totals = {"seen": len(events), "inserted": 0, "updated": 0, "skipped": 0, "errors": 0}
    for event in events:
        try:
            status = save_normalized_event(conn, columns, event)
            totals[status] += 1
        except Exception as exc:
            totals["errors"] += 1
            print(
                f"Normalized event generation failed: source={source} "
                f"raw_observation_id={event.get('raw_observation_id')} error={exc}",
                file=sys.stderr,
            )

    print(
        "Normalized events generation: "
        f"source={source} "
        f"seen={totals['seen']} "
        f"inserted={totals['inserted']} "
        f"updated={totals['updated']} "
        f"skipped={totals['skipped']} "
        f"errors={totals['errors']}"
    )
    return totals


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Generate World Pulse normalized events.")
    parser.add_argument(
        "--source",
        choices=["usgs", "wikipedia", "all"],
        default="all",
        help="Source to normalize.",
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

    sources = ["usgs", "wikipedia"] if args.source == "all" else [args.source]
    totals = {"seen": 0, "inserted": 0, "updated": 0, "skipped": 0, "errors": 0}

    with psycopg.connect(args.database_url) as conn:
        columns = table_columns(conn, "normalized_events")
        if not columns:
            print("normalized_events table was not found.", file=sys.stderr)
            return 1

        for source in sources:
            source_totals = generate_for_source(conn, columns, source)
            for key in totals:
                totals[key] += source_totals[key]

        conn.commit()

    print(
        "Normalized events generation completed: "
        f"source={args.source} "
        f"seen={totals['seen']} "
        f"inserted={totals['inserted']} "
        f"updated={totals['updated']} "
        f"skipped={totals['skipped']} "
        f"errors={totals['errors']}"
    )
    return 1 if totals["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
