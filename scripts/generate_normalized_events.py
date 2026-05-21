#!/usr/bin/env python3
import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import psycopg
from dotenv import load_dotenv
from psycopg.types.json import Jsonb


USGS_SOURCE_NAME = "USGS Earthquake Hazards Program"
WIKIPEDIA_SOURCE_NAME = "Wikipedia Pageviews"
CLOUDFLARE_SOURCE_NAME = "Cloudflare Radar"

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


def find_source_id(conn, source_name):
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM sources WHERE name = %s", (source_name,))
        row = cur.fetchone()
        return row[0] if row is not None else None


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

    with conn.cursor() as cur:
        insert_columns = list(values)
        placeholders = ", ".join(["%s"] * len(insert_columns))
        column_sql = ", ".join(insert_columns)
        update_columns = [
            column
            for column in insert_columns
            if column not in {"raw_observation_id", "event_type", "created_at"}
        ]
        if update_columns:
            conflict_sql = "DO UPDATE SET " + ", ".join(
                f"{column} = EXCLUDED.{column}" for column in update_columns
            )
            returning_sql = "RETURNING (xmax = 0) AS inserted"
        else:
            conflict_sql = "DO NOTHING"
            returning_sql = "RETURNING TRUE AS inserted"
        cur.execute(
            f"""
            INSERT INTO normalized_events ({column_sql})
            VALUES ({placeholders})
            ON CONFLICT (raw_observation_id, event_type)
            {conflict_sql}
            {returning_sql}
            """,
            [values[column] for column in insert_columns],
        )
        row = cur.fetchone()
        if row is None:
            return "skipped"
        return "inserted" if row[0] else "updated"


def fetch_usgs_raw_observations(conn, source_id, since_datetime=None):
    with conn.cursor() as cur:
        params = [source_id]
        window_sql = ""
        if since_datetime is not None:
            window_sql = "AND observed_at >= %s"
            params.append(since_datetime)
        cur.execute(
            f"""
            SELECT id, observed_at, raw_payload
            FROM raw_observations
            WHERE source_id = %s
              {window_sql}
            ORDER BY observed_at
            """,
            params,
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


def fetch_wikipedia_raw_observations(conn, source_id, since_datetime=None):
    with conn.cursor() as cur:
        params = [source_id]
        window_sql = ""
        if since_datetime is not None:
            window_sql = "AND observed_at >= %s"
            params.append(since_datetime)
        cur.execute(
            f"""
            SELECT id, observed_at, raw_payload
            FROM raw_observations
            WHERE source_id = %s
              AND raw_payload->>'dataset' = 'top_pageviews'
              {window_sql}
            ORDER BY observed_at
            """,
            params,
        )
        return cur.fetchall()


def fetch_cloudflare_raw_observations(conn, source_id, since_datetime=None):
    with conn.cursor() as cur:
        params = [source_id]
        window_sql = ""
        if since_datetime is not None:
            window_sql = "AND observed_at >= %s"
            params.append(since_datetime)
        cur.execute(
            f"""
            SELECT id, observed_at, raw_payload
            FROM raw_observations
            WHERE source_id = %s
              AND raw_payload->>'dataset' = 'cloudflare_radar_outages'
              {window_sql}
            ORDER BY observed_at
            """,
            params,
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


def parse_record_time(record):
    if not isinstance(record, dict):
        return None
    for key in [
        "startTime",
        "startDate",
        "start_time",
        "start",
        "detectedAt",
        "detected_at",
        "date",
        "timestamp",
    ]:
        value = record.get(key)
        if value is None:
            continue
        if isinstance(value, (int, float)):
            try:
                return datetime.fromtimestamp(value, tz=timezone.utc)
            except (OSError, ValueError):
                continue
        if not isinstance(value, str):
            continue
        normalized = value.strip()
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            continue
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    return None


def first_text(record, keys):
    if not isinstance(record, dict):
        return None
    for key in keys:
        value = record.get(key)
        if value:
            return str(value)
    return None


def first_location(record):
    value = first_text(
        record,
        [
            "location",
            "locationName",
            "countryName",
            "country",
            "asnName",
            "asn",
            "scope",
        ],
    )
    if value:
        return value
    for key in ["locationsDetails", "locations", "originsDetails", "origins"]:
        items = record.get(key) if isinstance(record, dict) else None
        if isinstance(items, list) and items:
            first = items[0]
            if isinstance(first, dict):
                return str(first.get("name") or first.get("code") or first.get("origin") or "reported scope")
            return str(first)
    return "reported scope"


def first_number(record, keys):
    if not isinstance(record, dict):
        return None
    for key in keys:
        value = record.get(key)
        if value is None:
            continue
        if isinstance(value, list):
            return float(len(value))
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def cloudflare_records(raw_payload):
    records = raw_payload.get("records")
    return records if isinstance(records, list) else []


def build_cloudflare_event(source_id, row):
    raw_observation_id, observed_at, raw_payload = row
    records = cloudflare_records(raw_payload)
    record = records[0] if records else {}

    location = first_location(record)

    event_time = parse_record_time(record) or observed_at
    magnitude_value = first_number(
        record,
        [
            "magnitude",
            "impact",
            "duration",
            "durationMinutes",
            "affectedNetworks",
            "affected_networks",
            "affectedLocations",
            "affected_locations",
        ],
    )

    event_type = "internet_outage_observation"
    annotation_type = first_text(record, ["annotationType", "type", "outageType"])
    if annotation_type and "anomal" in annotation_type.lower():
        event_type = "internet_anomaly_observation"

    title_kind = "Internet anomaly observation" if event_type == "internet_anomaly_observation" else "Internet outage observation"

    return {
        "raw_observation_id": raw_observation_id,
        "source_id": source_id,
        "event_type": event_type,
        "category": "internet",
        "title": f"{title_kind} for {location}",
        "event_time": event_time,
        "magnitude_value": magnitude_value,
        "location_label": location,
        "latitude": None,
        "longitude": None,
        "anomaly_score": None,
        "normalized_payload": {
            "provider": "Cloudflare Radar",
            "dataset": raw_payload.get("dataset"),
            "endpoint_url": raw_payload.get("endpoint_url"),
            "record_count": raw_payload.get("record_count"),
            "record": record,
        },
    }


def isoformat_z(value):
    if value is None:
        return "all"
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_since_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--since-date must use YYYY-MM-DD format") from exc


def resolve_since_datetime(args):
    if args.since_date is not None:
        return datetime.combine(args.since_date, datetime.min.time(), tzinfo=timezone.utc)
    if args.days is not None:
        if args.days <= 0:
            raise ValueError("--days must be greater than zero")
        since_date = datetime.now(timezone.utc).date() - timedelta(days=args.days)
        return datetime.combine(since_date, datetime.min.time(), tzinfo=timezone.utc)
    return None


def generate_for_source(conn, columns, source, since_datetime=None):
    started = time.monotonic()
    window_start = isoformat_z(since_datetime)
    if source == "usgs":
        source_id = get_source_id(conn, USGS_SOURCE_NAME)
        rows = fetch_usgs_raw_observations(conn, source_id, since_datetime)
        baseline = fetch_baseline(conn, source_id, "usgs_daily_max_magnitude")
        events = [build_usgs_event(source_id, row, baseline) for row in rows]
    elif source == "wikipedia":
        source_id = get_source_id(conn, WIKIPEDIA_SOURCE_NAME)
        rows = fetch_wikipedia_raw_observations(conn, source_id, since_datetime)
        baseline = fetch_baseline(conn, source_id, "wikipedia_daily_top1000_total_views")
        events = [build_wikipedia_event(source_id, row, baseline) for row in rows]
    elif source == "cloudflare":
        source_id = find_source_id(conn, CLOUDFLARE_SOURCE_NAME)
        if source_id is None:
            elapsed = time.monotonic() - started
            print(
                "Normalized events generation: source=cloudflare "
                f"window_start={window_start} seen=0 inserted=0 updated=0 skipped=0 "
                f"errors=0 elapsed_seconds={elapsed:.2f}"
            )
            return {"seen": 0, "inserted": 0, "updated": 0, "skipped": 0, "errors": 0}
        rows = fetch_cloudflare_raw_observations(conn, source_id, since_datetime)
        events = [build_cloudflare_event(source_id, row) for row in rows]
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

    elapsed = time.monotonic() - started
    print(
        "Normalized events generation: "
        f"source={source} "
        f"window_start={window_start} "
        f"seen={totals['seen']} "
        f"inserted={totals['inserted']} "
        f"updated={totals['updated']} "
        f"skipped={totals['skipped']} "
        f"errors={totals['errors']} "
        f"elapsed_seconds={elapsed:.2f}"
    )
    return totals


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Generate World Pulse normalized events.")
    parser.add_argument(
        "--source",
        choices=["usgs", "wikipedia", "cloudflare", "all"],
        default="all",
        help="Source to normalize.",
    )
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL"),
        help="PostgreSQL connection URL. Defaults to DATABASE_URL.",
    )
    window_group = parser.add_mutually_exclusive_group()
    window_group.add_argument(
        "--since-date",
        type=parse_since_date,
        default=None,
        help="Only process raw observations observed on or after this UTC date.",
    )
    window_group.add_argument(
        "--days",
        type=int,
        default=None,
        help="Only process raw observations since UTC today minus this many days.",
    )
    args = parser.parse_args()

    if not args.database_url:
        print("DATABASE_URL is required.", file=sys.stderr)
        return 2

    try:
        since_datetime = resolve_since_datetime(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    sources = ["usgs", "wikipedia", "cloudflare"] if args.source == "all" else [args.source]
    totals = {"seen": 0, "inserted": 0, "updated": 0, "skipped": 0, "errors": 0}
    started = time.monotonic()

    with psycopg.connect(args.database_url) as conn:
        columns = table_columns(conn, "normalized_events")
        if not columns:
            print("normalized_events table was not found.", file=sys.stderr)
            return 1

        for source in sources:
            source_totals = generate_for_source(conn, columns, source, since_datetime)
            for key in totals:
                totals[key] += source_totals[key]

        conn.commit()

    elapsed = time.monotonic() - started
    print(
        "Normalized events generation completed: "
        f"source={args.source} "
        f"window_start={isoformat_z(since_datetime)} "
        f"seen={totals['seen']} "
        f"inserted={totals['inserted']} "
        f"updated={totals['updated']} "
        f"skipped={totals['skipped']} "
        f"errors={totals['errors']} "
        f"elapsed_seconds={elapsed:.2f}"
    )
    return 1 if totals["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
