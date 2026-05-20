#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

import psycopg
import requests
from dotenv import load_dotenv
from psycopg.types.json import Jsonb


SOURCE_NAME = "Cloudflare Radar"
SOURCE_TYPE = "api"
BASE_URL = "https://api.cloudflare.com/client/v4/radar/"
SOURCE_DESCRIPTION = "Cloudflare Radar public Internet outage and anomaly observations."

DATASET_KEY = "cloudflare_radar_outages"
ENDPOINTS = {
    "outages": "https://api.cloudflare.com/client/v4/radar/annotations/outages",
}


def canonical_payload_hash(payload):
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def isoformat_z(value):
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_time(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value, tz=timezone.utc)
        except (OSError, ValueError):
            return None
    if not isinstance(value, str):
        return None

    normalized = value.strip()
    if not normalized:
        return None
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"

    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


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


def get_source_id(conn):
    columns = table_columns(conn, "sources")
    values = {
        "name": SOURCE_NAME,
        "source_type": SOURCE_TYPE,
        "base_url": BASE_URL,
    }
    if "description" in columns:
        values["description"] = SOURCE_DESCRIPTION

    insert_columns = list(values)
    placeholders = ", ".join(["%s"] * len(insert_columns))
    column_sql = ", ".join(insert_columns)
    update_columns = [column for column in insert_columns if column != "name"]
    update_sql = ", ".join(f"{column} = EXCLUDED.{column}" for column in update_columns)

    with conn.cursor() as cur:
        cur.execute(
            f"""
            INSERT INTO sources ({column_sql})
            VALUES ({placeholders})
            ON CONFLICT (name)
            DO UPDATE SET {update_sql}
            RETURNING id
            """,
            [values[column] for column in insert_columns],
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


def extract_records(payload):
    candidates = [
        payload.get("annotations") if isinstance(payload, dict) else None,
        payload.get("result", {}).get("annotations") if isinstance(payload, dict) else None,
        payload.get("result") if isinstance(payload, dict) else None,
        payload,
    ]
    for candidate in candidates:
        if isinstance(candidate, list):
            return candidate
    return []


def record_observed_at(record):
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
        parsed = parse_time(record.get(key))
        if parsed is not None:
            return parsed
    return None


def latest_observed_at(records, fetched_at):
    observed_times = []
    for record in records:
        observed_at = record_observed_at(record)
        if observed_at is not None:
            observed_times.append(observed_at)
    return max(observed_times) if observed_times else fetched_at


def stable_payload_for_hash(raw_payload):
    return {key: value for key, value in raw_payload.items() if key != "fetched_at"}


def fetch_radar_payload(endpoint_url, token, limit):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    params = {"dateRange": "7d", "limit": limit}
    response = requests.get(endpoint_url, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    return response.json(), response.status_code, dict(response.headers), params


def build_raw_payload(dataset, endpoint_url, fetched_at, records, raw_response):
    return {
        "dataset": dataset,
        "endpoint_url": endpoint_url,
        "fetched_at": isoformat_z(fetched_at),
        "record_count": len(records),
        "records": records,
        "raw_response": raw_response,
    }


def insert_raw_observation(
    conn,
    source_id,
    ingestion_run_id,
    http_status,
    response_headers,
    request_params,
    raw_payload,
):
    payload_hash = canonical_payload_hash(stable_payload_for_hash(raw_payload))
    fetched_at = datetime.fromisoformat(raw_payload["fetched_at"].replace("Z", "+00:00"))
    observed_at = latest_observed_at(raw_payload["records"], fetched_at)

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
                Jsonb(raw_payload),
            ),
        )
        row = cur.fetchone()
        if row is None:
            return False

        lineage = {
            "provider": "Cloudflare Radar",
            "dataset": raw_payload["dataset"],
            "endpoint_url": raw_payload["endpoint_url"],
            "request_method": "GET",
            "request_params": request_params,
            "http_status": http_status,
            "response_headers": response_headers,
            "payload_hash": payload_hash,
            "record_count": raw_payload["record_count"],
            "fetched_at": raw_payload["fetched_at"],
        }
        cur.execute(
            """
            INSERT INTO source_lineage (
                raw_observation_id,
                source_id,
                ingestion_run_id,
                lineage_note
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                row[0],
                source_id,
                ingestion_run_id,
                json.dumps(lineage, sort_keys=True, separators=(",", ":")),
            ),
        )
    return True


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Ingest Cloudflare Radar observations.")
    parser.add_argument(
        "--dataset",
        choices=["outages"],
        default="outages",
        help="Cloudflare Radar dataset to ingest.",
    )
    parser.add_argument("--limit", type=int, default=100, help="Maximum records to request.")
    parser.add_argument("--dry-run", action="store_true", help="Fetch and summarize without saving.")
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL"),
        help="PostgreSQL connection URL. Defaults to DATABASE_URL.",
    )
    args = parser.parse_args()

    token = os.environ.get("CLOUDFLARE_API_TOKEN")
    if not token:
        print("Cloudflare Radar ingestion skipped: CLOUDFLARE_API_TOKEN is not set")
        return 0
    if args.limit <= 0:
        print("--limit must be greater than zero.", file=sys.stderr)
        return 2
    if not args.dry_run and not args.database_url:
        print("DATABASE_URL is required.", file=sys.stderr)
        return 2

    endpoint_url = ENDPOINTS[args.dataset]
    dataset_key = DATASET_KEY
    seen = 0
    inserted = 0
    skipped_duplicates = 0
    errors = 0
    run_id = None

    try:
        fetched_at = datetime.now(timezone.utc)
        response_payload, http_status, response_headers, request_params = fetch_radar_payload(
            endpoint_url,
            token,
            args.limit,
        )
        records = extract_records(response_payload)
        seen = len(records)
        raw_payload = build_raw_payload(
            dataset_key,
            endpoint_url,
            fetched_at,
            records,
            response_payload,
        )

        if args.dry_run:
            print(
                "Cloudflare Radar ingestion dry run: "
                f"dataset={args.dataset} "
                f"seen={seen} "
                f"record_count={len(records)} "
                "errors=0"
            )
            return 0

        with psycopg.connect(args.database_url) as conn:
            source_id = get_source_id(conn)
            run_id = start_ingestion_run(conn, source_id, endpoint_url)
            conn.commit()

            was_inserted = insert_raw_observation(
                conn,
                source_id,
                run_id,
                http_status,
                response_headers,
                request_params,
                raw_payload,
            )
            if was_inserted:
                inserted = 1
            else:
                skipped_duplicates = 1

            finish_ingestion_run(conn, run_id, "completed", seen, inserted)
            conn.commit()

    except Exception as exc:
        errors = 1
        if run_id is not None and args.database_url:
            with psycopg.connect(args.database_url) as conn:
                finish_ingestion_run(conn, run_id, "failed", seen, inserted, str(exc))
                conn.commit()
        print(f"Cloudflare Radar ingestion failed: {exc}", file=sys.stderr)
        return 1

    print(
        "Cloudflare Radar ingestion completed: "
        f"dataset={args.dataset} "
        f"seen={seen} "
        f"inserted={inserted} "
        f"skipped_duplicates={skipped_duplicates} "
        f"record_count={seen} "
        f"errors={errors}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
