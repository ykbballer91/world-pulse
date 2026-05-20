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


SOURCE_NAME = "Open Notify"
SOURCE_TYPE = "public_observation_feed"
BASE_URL = "http://api.open-notify.org"

DATASETS = {
    "iss": "http://api.open-notify.org/iss-now.json",
    "astros": "http://api.open-notify.org/astros.json",
}


def canonical_payload_hash(payload):
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def isoformat_z(value):
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def selected_datasets(dataset):
    if dataset == "all":
        return DATASETS.items()
    return [(dataset, DATASETS[dataset])]


def get_source_id(conn):
    with conn.cursor() as cur:
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


def fetch_payload(endpoint_url):
    response = requests.get(endpoint_url, timeout=30)
    response.raise_for_status()
    return response.json(), response.status_code, dict(response.headers)


def observed_at_for_payload(raw_payload):
    fetched_at = datetime.fromisoformat(raw_payload["fetched_at"].replace("Z", "+00:00"))
    if raw_payload["dataset"] != "iss":
        return fetched_at

    timestamp = raw_payload["records"].get("timestamp")
    if timestamp is None:
        return fetched_at

    try:
        return datetime.fromtimestamp(float(timestamp), tz=timezone.utc)
    except (TypeError, ValueError, OSError):
        return fetched_at


def build_raw_payload(dataset, endpoint_url, fetched_at, payload):
    return {
        "dataset": dataset,
        "endpoint_url": endpoint_url,
        "fetched_at": isoformat_z(fetched_at),
        "records": payload,
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
    observed_at = observed_at_for_payload(raw_payload)

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

    parser = argparse.ArgumentParser(description="Ingest Open Notify raw observations.")
    parser.add_argument(
        "--dataset",
        choices=["iss", "astros", "all"],
        default="all",
        help="Open Notify dataset to ingest.",
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
    run_id = None

    try:
        fetched = []
        for dataset, endpoint_url in endpoints:
            fetched_at = datetime.now(timezone.utc)
            payload, http_status, response_headers = fetch_payload(endpoint_url)
            raw_payload = build_raw_payload(dataset, endpoint_url, fetched_at, payload)
            fetched.append((raw_payload, http_status, response_headers))
            seen_datasets += 1

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
        print(f"Open Notify ingestion failed: {exc}", file=sys.stderr)
        return 1

    print(
        "Open Notify ingestion completed: "
        f"dataset={args.dataset} "
        f"seen_datasets={seen_datasets} "
        f"inserted={inserted} "
        f"skipped_duplicates={skipped_duplicates}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
