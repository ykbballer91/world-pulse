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


SOURCE_KEY = "noaa_swpc"
SOURCE_NAME = "NOAA SWPC"
SOURCE_TYPE = "public_observation_feed"
BASE_URL = "https://services.swpc.noaa.gov"

DATASETS = {
    "kp": "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json",
    "xray": "https://services.swpc.noaa.gov/json/goes/primary/xrays-7-day.json",
}


def canonical_payload_hash(payload):
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def parse_observed_at(record):
    value = record.get("time_tag") or record.get("time_tag_utc") or record.get("observed_at")
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)

    if not isinstance(value, str):
        return None

    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"

    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def isoformat_z(value):
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def selected_datasets(dataset):
    if dataset == "all":
        return DATASETS.items()
    return [(dataset, DATASETS[dataset])]


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

    with conn.cursor() as cur:
        if "source_key" in columns:
            cur.execute(
                """
                INSERT INTO sources (source_key, name, source_type, base_url)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (source_key)
                DO UPDATE SET name = EXCLUDED.name,
                              source_type = EXCLUDED.source_type,
                              base_url = EXCLUDED.base_url
                RETURNING id
                """,
                (SOURCE_KEY, SOURCE_NAME, SOURCE_TYPE, BASE_URL),
            )
        else:
            cur.execute(
                """
                INSERT INTO sources (name, source_type, base_url)
                VALUES (%s, %s, %s)
                ON CONFLICT (name)
                DO UPDATE SET source_type = EXCLUDED.source_type,
                              base_url = EXCLUDED.base_url
                RETURNING id
                """,
                (SOURCE_NAME, SOURCE_TYPE, BASE_URL),
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


def fetch_records(endpoint_url):
    response = requests.get(endpoint_url, timeout=30)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        raise ValueError(f"NOAA SWPC response was not a list: {endpoint_url}")
    return payload, response.status_code, dict(response.headers)


def latest_observed_at(records, fetched_at):
    observed_times = []
    for record in records:
        observed_at = parse_observed_at(record)
        if observed_at is not None:
            observed_times.append(observed_at)
    if not observed_times:
        return fetched_at
    return max(observed_times)


def build_raw_payload(dataset, endpoint_url, fetched_at, records):
    return {
        "dataset": dataset,
        "endpoint_url": endpoint_url,
        "fetched_at": isoformat_z(fetched_at),
        "record_count": len(records),
        "records": records,
    }


def insert_raw_observation(
    conn,
    source_id,
    ingestion_run_id,
    http_status,
    response_headers,
    raw_payload,
):
    payload_hash = canonical_payload_hash(raw_payload)
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
            "dataset": raw_payload["dataset"],
            "endpoint_url": raw_payload["endpoint_url"],
            "request_method": "GET",
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

    parser = argparse.ArgumentParser(description="Ingest NOAA SWPC raw observations.")
    parser.add_argument(
        "--dataset",
        choices=["kp", "xray", "all"],
        default="all",
        help="NOAA SWPC dataset to ingest.",
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

    endpoints = list(selected_datasets(args.dataset))
    request_urls = ",".join(endpoint_url for _, endpoint_url in endpoints)
    seen_datasets = 0
    inserted = 0
    skipped_duplicates = 0
    total_records = 0
    run_id = None

    try:
        fetched = []
        for dataset, endpoint_url in endpoints:
            fetched_at = datetime.now(timezone.utc)
            records, http_status, response_headers = fetch_records(endpoint_url)
            raw_payload = build_raw_payload(dataset, endpoint_url, fetched_at, records)
            fetched.append((raw_payload, http_status, response_headers))
            seen_datasets += 1
            total_records += len(records)

        with psycopg.connect(args.database_url) as conn:
            source_id = get_source_id(conn)
            run_id = start_ingestion_run(conn, source_id, request_urls)
            conn.commit()

            for raw_payload, http_status, response_headers in fetched:
                was_inserted = insert_raw_observation(
                    conn,
                    source_id,
                    run_id,
                    http_status,
                    response_headers,
                    raw_payload,
                )
                if was_inserted:
                    inserted += 1
                else:
                    skipped_duplicates += 1

            finish_ingestion_run(conn, run_id, "completed", seen_datasets, inserted)
            conn.commit()

    except Exception as exc:
        if run_id is not None:
            with psycopg.connect(args.database_url) as conn:
                finish_ingestion_run(conn, run_id, "failed", seen_datasets, inserted, str(exc))
                conn.commit()
        print(f"NOAA SWPC ingestion failed: {exc}", file=sys.stderr)
        return 1

    print(
        "NOAA SWPC ingestion completed: "
        f"dataset={args.dataset} "
        f"seen_datasets={seen_datasets} "
        f"inserted={inserted} "
        f"skipped_duplicates={skipped_duplicates} "
        f"total_records={total_records}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
