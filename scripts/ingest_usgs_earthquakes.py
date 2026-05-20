#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import psycopg
import requests
from dotenv import load_dotenv
from psycopg.types.json import Jsonb


SOURCE_NAME = "USGS Earthquake Hazards Program"
SOURCE_TYPE = "public_observation_feed"
USGS_QUERY_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"


def canonical_payload_hash(payload):
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def parse_usgs_millis(value):
    if value is None:
        return None
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc)


def isoformat_z(value):
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_request_url(hours, min_magnitude):
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=hours)
    params = {
        "format": "geojson",
        "minmagnitude": min_magnitude,
        "starttime": isoformat_z(start_time),
        "endtime": isoformat_z(end_time),
        "orderby": "time",
    }
    return f"{USGS_QUERY_URL}?{urlencode(params)}"


def get_source_id(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO sources (name, source_type, base_url)
            VALUES (%s, %s, %s)
            ON CONFLICT (name)
            DO UPDATE SET source_type = EXCLUDED.source_type, base_url = EXCLUDED.base_url
            RETURNING id
            """,
            (SOURCE_NAME, SOURCE_TYPE, USGS_QUERY_URL),
        )
        return cur.fetchone()[0]


def start_ingestion_run(conn, source_id, request_url):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO ingestion_runs (source_id, request_url)
            VALUES (%s, %s)
            RETURNING id
            """,
            (source_id, request_url),
        )
        return cur.fetchone()[0]


def finish_ingestion_run(conn, run_id, status, seen, inserted, error_message=None):
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE ingestion_runs
            SET completed_at = now(),
                status = %s,
                observations_seen = %s,
                observations_inserted = %s,
                error_message = %s
            WHERE id = %s
            """,
            (status, seen, inserted, error_message, run_id),
        )


def insert_raw_observation(conn, source_id, ingestion_run_id, feature):
    payload_hash = canonical_payload_hash(feature)
    observed_at = parse_usgs_millis(feature.get("properties", {}).get("time"))

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO raw_observations (
                payload_hash,
                source_id,
                ingestion_run_id,
                observed_at,
                raw_payload
            )
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (source_id, payload_hash) DO NOTHING
            RETURNING id
            """,
            (
                payload_hash,
                source_id,
                ingestion_run_id,
                observed_at,
                Jsonb(feature),
            ),
        )
        row = cur.fetchone()
        if row is None:
            return False

        raw_observation_id = row[0]
        cur.execute(
            """
            INSERT INTO source_lineage (
                raw_observation_id,
                source_id,
                ingestion_run_id
            )
            VALUES (%s, %s, %s)
            """,
            (raw_observation_id, source_id, ingestion_run_id),
        )
        return True


def is_at_or_above_min_magnitude(feature, min_magnitude):
    magnitude = feature.get("properties", {}).get("mag")
    if magnitude is None:
        return False
    return magnitude >= min_magnitude


def fetch_usgs_features(request_url):
    response = requests.get(request_url, timeout=30)
    response.raise_for_status()
    payload = response.json()
    features = payload.get("features")
    if not isinstance(features, list):
        raise ValueError("USGS response did not include a features list")
    return features


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Ingest USGS earthquake observations.")
    parser.add_argument("--hours", type=float, default=24, help="Lookback window in hours.")
    parser.add_argument(
        "--min-magnitude",
        type=float,
        default=4.0,
        help="Minimum earthquake magnitude to ingest.",
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

    if args.hours <= 0:
        print("--hours must be greater than zero.", file=sys.stderr)
        return 2

    request_url = build_request_url(args.hours, args.min_magnitude)
    seen = 0
    skipped_below_min_magnitude = 0
    inserted = 0
    run_id = None

    try:
        features = fetch_usgs_features(request_url)
        seen = len(features)

        with psycopg.connect(args.database_url) as conn:
            source_id = get_source_id(conn)
            run_id = start_ingestion_run(conn, source_id, request_url)
            conn.commit()

            for feature in features:
                if not is_at_or_above_min_magnitude(feature, args.min_magnitude):
                    skipped_below_min_magnitude += 1
                    continue
                if insert_raw_observation(conn, source_id, run_id, feature):
                    inserted += 1

            finish_ingestion_run(conn, run_id, "completed", seen, inserted)
            conn.commit()

    except Exception as exc:
        if run_id is not None:
            with psycopg.connect(args.database_url) as conn:
                finish_ingestion_run(conn, run_id, "failed", seen, inserted, str(exc))
                conn.commit()
        print(f"USGS ingestion failed: {exc}", file=sys.stderr)
        return 1

    print(
        "USGS ingestion completed: "
        f"seen={seen} "
        f"skipped_below_min_magnitude={skipped_below_min_magnitude} "
        f"inserted={inserted}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
