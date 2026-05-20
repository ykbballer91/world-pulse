#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timedelta, timezone

import psycopg
import requests
from dotenv import load_dotenv
from psycopg.types.json import Jsonb


SOURCE_NAME = "Wikipedia Pageviews"
SOURCE_TYPE = "public_attention_feed"
BASE_URL = "https://wikimedia.org/api/rest_v1/metrics/pageviews"
DATASET = "top_pageviews"


def canonical_payload_hash(payload):
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def stable_payload_for_hash(raw_payload):
    return {key: value for key, value in raw_payload.items() if key != "fetched_at"}


def isoformat_z(value):
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def default_date():
    return (datetime.now(timezone.utc).date() - timedelta(days=2)).isoformat()


def parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--date must use YYYY-MM-DD format") from exc


def build_endpoint_url(project, access, target_date):
    return (
        f"{BASE_URL}/top/{project}/{access}/"
        f"{target_date:%Y}/{target_date:%m}/{target_date:%d}"
    )


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
    headers = {
        "User-Agent": "WorldPulse/0.1 (raw observation ingestion; no prediction or advice)"
    }
    response = requests.get(endpoint_url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json(), response.status_code, dict(response.headers)


def extract_records(payload):
    items = payload.get("items")
    if not isinstance(items, list) or not items:
        return []

    articles = items[0].get("articles")
    if not isinstance(articles, list):
        return []
    return articles


def build_raw_payload(project, access, target_date, endpoint_url, fetched_at, records):
    date_text = target_date.isoformat()
    return {
        "dataset": DATASET,
        "project": project,
        "access": access,
        "date": date_text,
        "endpoint_url": endpoint_url,
        "fetched_at": isoformat_z(fetched_at),
        "record_count": len(records),
        "records": records,
    }


def observed_at_for_date(target_date):
    return datetime(
        target_date.year,
        target_date.month,
        target_date.day,
        tzinfo=timezone.utc,
    )


def insert_raw_observation(
    conn,
    source_id,
    ingestion_run_id,
    http_status,
    response_headers,
    raw_payload,
    observed_at,
):
    payload_hash = canonical_payload_hash(stable_payload_for_hash(raw_payload))

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id
            FROM raw_observations
            WHERE source_id = %s
              AND raw_payload->>'dataset' = %s
              AND raw_payload->>'project' = %s
              AND raw_payload->>'access' = %s
              AND raw_payload->>'date' = %s
            LIMIT 1
            """,
            (
                source_id,
                raw_payload["dataset"],
                raw_payload["project"],
                raw_payload["access"],
                raw_payload["date"],
            ),
        )
        if cur.fetchone() is not None:
            return False

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
            "project": raw_payload["project"],
            "access": raw_payload["access"],
            "date": raw_payload["date"],
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

    parser = argparse.ArgumentParser(description="Ingest Wikipedia top pageviews raw observations.")
    parser.add_argument(
        "--date",
        type=parse_date,
        default=parse_date(default_date()),
        help="Pageviews date in YYYY-MM-DD format. Defaults to two days ago in UTC.",
    )
    parser.add_argument(
        "--project",
        default="en.wikipedia",
        help="Wikimedia project. Defaults to en.wikipedia.",
    )
    parser.add_argument(
        "--access",
        default="all-access",
        help="Access method. Defaults to all-access.",
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

    endpoint_url = build_endpoint_url(args.project, args.access, args.date)
    inserted = 0
    skipped_duplicates = 0
    record_count = 0
    run_id = None

    try:
        fetched_at = datetime.now(timezone.utc)
        payload, http_status, response_headers = fetch_payload(endpoint_url)
        records = extract_records(payload)
        record_count = len(records)
        raw_payload = build_raw_payload(
            args.project,
            args.access,
            args.date,
            endpoint_url,
            fetched_at,
            records,
        )
        observed_at = observed_at_for_date(args.date)

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
                raw_payload,
                observed_at,
            )
            if was_inserted:
                inserted = 1
            else:
                skipped_duplicates = 1

            finish_ingestion_run(conn, run_id, "completed", 1, inserted)
            conn.commit()

    except requests.HTTPError as exc:
        if run_id is not None:
            with psycopg.connect(args.database_url) as conn:
                finish_ingestion_run(conn, run_id, "failed", 1, inserted, str(exc))
                conn.commit()
        response = exc.response
        if response is not None and response.status_code == 404:
            print(
                "Wikipedia Pageviews ingestion failed: 404 Not Found\n"
                f"endpoint_url={endpoint_url}\n"
                f"project={args.project}\n"
                f"access={args.access}\n"
                f"date={args.date.isoformat()}\n"
                "hint=Daily top pageviews may not be generated yet; try a date 1-3 days ago.",
                file=sys.stderr,
            )
        else:
            print(f"Wikipedia Pageviews ingestion failed: {exc}", file=sys.stderr)
        return 1

    except Exception as exc:
        if run_id is not None:
            with psycopg.connect(args.database_url) as conn:
                finish_ingestion_run(conn, run_id, "failed", 1, inserted, str(exc))
                conn.commit()
        print(f"Wikipedia Pageviews ingestion failed: {exc}", file=sys.stderr)
        return 1

    print(
        "Wikipedia Pageviews ingestion completed: "
        f"project={args.project} "
        f"date={args.date.isoformat()} "
        f"inserted={inserted} "
        f"skipped_duplicates={skipped_duplicates} "
        f"record_count={record_count}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
