#!/usr/bin/env python3
import argparse
import json
import os
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import psycopg
from dotenv import load_dotenv
from psycopg.types.json import Jsonb


USGS_SOURCE_NAME = "USGS Earthquake Hazards Program"
WIKIPEDIA_SOURCE_NAME = "Wikipedia Pageviews"

JSON_COLUMNS = [
    "distribution_payload",
    "payload",
    "metadata",
    "distribution",
    "stats",
    "values",
]


def utc_midnight(value):
    return datetime(value.year, value.month, value.day, tzinfo=timezone.utc)


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


def get_source_id(conn, source_name):
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM sources WHERE name = %s", (source_name,))
        row = cur.fetchone()
        if row is None:
            raise ValueError(f"source not found: {source_name}")
        return row[0]


def summary(values):
    if not values:
        return {
            "count": 0,
            "min": None,
            "max": None,
            "avg": None,
            "median": None,
            "stddev": None,
            "p50": None,
            "p75": None,
            "p90": None,
            "p95": None,
            "p99": None,
        }
    sorted_values = sorted(values)
    return {
        "count": len(values),
        "min": sorted_values[0],
        "max": sorted_values[-1],
        "avg": sum(values) / len(values),
        "median": statistics.median(values),
        "stddev": statistics.pstdev(values) if len(values) >= 2 else None,
        "p50": percentile(sorted_values, 50),
        "p75": percentile(sorted_values, 75),
        "p90": percentile(sorted_values, 90),
        "p95": percentile(sorted_values, 95),
        "p99": percentile(sorted_values, 99),
    }


def percentile(sorted_values, percentile_value):
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return sorted_values[0]

    rank = (len(sorted_values) - 1) * (percentile_value / 100)
    lower_index = int(rank)
    upper_index = min(lower_index + 1, len(sorted_values) - 1)
    weight = rank - lower_index
    return sorted_values[lower_index] * (1 - weight) + sorted_values[upper_index] * weight


def build_distribution_payload(source_name, metric_key, window_start, window_end, daily_values):
    values = [item["value"] for item in daily_values if item["value"] is not None]
    return {
        "source": source_name,
        "metric_key": metric_key,
        "window_start": isoformat_z(window_start),
        "window_end": isoformat_z(window_end),
        "sample_count": len(values),
        "values": values,
        "daily_values": daily_values,
        "summary": summary(values),
    }


def fetch_usgs_daily_metrics(conn, source_id, window_start, window_end):
    daily_magnitudes = defaultdict(list)

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT observed_at, raw_payload
            FROM raw_observations
            WHERE source_id = %s
              AND observed_at >= %s
              AND observed_at < %s
            ORDER BY observed_at
            """,
            (source_id, window_start, window_end),
        )
        rows = cur.fetchall()

    for observed_at, raw_payload in rows:
        if observed_at is None:
            continue
        magnitude = raw_payload.get("properties", {}).get("mag")
        if magnitude is None:
            continue
        try:
            daily_magnitudes[observed_at.date().isoformat()].append(float(magnitude))
        except (TypeError, ValueError):
            continue

    metrics = {
        "usgs_daily_m4_count": [],
        "usgs_daily_max_magnitude": [],
        "usgs_daily_avg_magnitude": [],
    }
    for day in sorted(daily_magnitudes):
        magnitudes = daily_magnitudes[day]
        metrics["usgs_daily_m4_count"].append({"date": day, "value": len(magnitudes)})
        metrics["usgs_daily_max_magnitude"].append({"date": day, "value": max(magnitudes)})
        metrics["usgs_daily_avg_magnitude"].append(
            {"date": day, "value": sum(magnitudes) / len(magnitudes)}
        )

    return metrics


def article_views(article):
    views = article.get("views")
    try:
        return int(views)
    except (TypeError, ValueError):
        return 0


def is_excluded_wikipedia_title(article):
    title = article.get("article")
    return title in {"Main_Page", "Special:Search"}


def fetch_wikipedia_daily_metrics(conn, source_id, window_start, window_end):
    rows_by_date = {}

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT raw_payload
            FROM raw_observations
            WHERE source_id = %s
              AND raw_payload->>'dataset' = 'top_pageviews'
              AND observed_at >= %s
              AND observed_at < %s
            ORDER BY raw_payload->>'date'
            """,
            (source_id, window_start, window_end),
        )
        rows = cur.fetchall()

    for (raw_payload,) in rows:
        date_text = raw_payload.get("date")
        records = raw_payload.get("records")
        if not date_text or not isinstance(records, list):
            continue
        rows_by_date[date_text] = records

    metrics = {
        "wikipedia_daily_top1000_total_views": [],
        "wikipedia_daily_top10_total_views": [],
        "wikipedia_daily_top10_total_views_excluding_main_page": [],
    }
    for day in sorted(rows_by_date):
        records = rows_by_date[day]
        top1000_total = sum(article_views(article) for article in records[:1000])
        top10_total = sum(article_views(article) for article in records[:10])
        filtered_records = [
            article for article in records if not is_excluded_wikipedia_title(article)
        ]
        top10_excluding_main = sum(article_views(article) for article in filtered_records[:10])

        metrics["wikipedia_daily_top1000_total_views"].append(
            {"date": day, "value": top1000_total}
        )
        metrics["wikipedia_daily_top10_total_views"].append(
            {"date": day, "value": top10_total}
        )
        metrics["wikipedia_daily_top10_total_views_excluding_main_page"].append(
            {"date": day, "value": top10_excluding_main}
        )

    return metrics


def choose_json_column(columns):
    for column in JSON_COLUMNS:
        if column in columns:
            return column
    return None


def existing_baseline_exists(conn, columns, source_id, metric_key, window_start, window_end):
    required = {"source_id", "metric_key", "window_start", "window_end"}
    if not required.issubset(columns):
        return False

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT 1
            FROM baseline_distributions
            WHERE source_id = %s
              AND metric_key = %s
              AND window_start = %s
              AND window_end = %s
            LIMIT 1
            """,
            (source_id, metric_key, window_start, window_end),
        )
        return cur.fetchone() is not None


def assign_if_column(values, columns, column, value):
    if column in columns:
        values[column] = value


def build_baseline_values(columns, source_id, metric_key, window_start, window_end, payload):
    values = {}
    json_column = choose_json_column(columns)

    assign_if_column(values, columns, "source_id", source_id)
    assign_if_column(values, columns, "metric_key", metric_key)
    assign_if_column(values, columns, "window_start", window_start)
    assign_if_column(values, columns, "window_end", window_end)
    assign_if_column(values, columns, "sample_count", payload["sample_count"])
    assign_if_column(values, columns, "n", payload["sample_count"])
    assign_if_column(values, columns, "count", payload["sample_count"])
    assign_if_column(values, columns, "min_value", payload["summary"]["min"])
    assign_if_column(values, columns, "max_value", payload["summary"]["max"])
    assign_if_column(values, columns, "avg_value", payload["summary"]["avg"])
    assign_if_column(values, columns, "mean_value", payload["summary"]["avg"])
    assign_if_column(values, columns, "median_value", payload["summary"]["median"])
    assign_if_column(values, columns, "stddev_value", payload["summary"]["stddev"])
    assign_if_column(values, columns, "p50_value", payload["summary"]["p50"])
    assign_if_column(values, columns, "p75_value", payload["summary"]["p75"])
    assign_if_column(values, columns, "p90_value", payload["summary"]["p90"])
    assign_if_column(values, columns, "p95_value", payload["summary"]["p95"])
    assign_if_column(values, columns, "p99_value", payload["summary"]["p99"])
    assign_if_column(values, columns, "created_at", datetime.now(timezone.utc))
    assign_if_column(values, columns, "updated_at", datetime.now(timezone.utc))

    if json_column is not None:
        values[json_column] = Jsonb(payload)

    return values


def save_baseline(conn, columns, source_id, metric_key, window_start, window_end, payload):
    if not {"source_id", "metric_key", "window_start", "window_end"}.issubset(columns):
        return "skipped"

    values = build_baseline_values(
        columns,
        source_id,
        metric_key,
        window_start,
        window_end,
        payload,
    )
    if not values:
        return "skipped"

    baseline_exists = existing_baseline_exists(
        conn,
        columns,
        source_id,
        metric_key,
        window_start,
        window_end,
    )

    with conn.cursor() as cur:
        if baseline_exists:
            update_values = {
                column: value for column, value in values.items() if column not in {"created_at"}
            }
            assignments = ", ".join(f"{column} = %s" for column in update_values)
            if not assignments:
                return "skipped"
            cur.execute(
                f"""
                UPDATE baseline_distributions
                SET {assignments}
                WHERE source_id = %s
                  AND metric_key = %s
                  AND window_start = %s
                  AND window_end = %s
                """,
                [
                    *update_values.values(),
                    source_id,
                    metric_key,
                    window_start,
                    window_end,
                ],
            )
            return "updated"

        insert_columns = list(values)
        placeholders = ", ".join(["%s"] * len(insert_columns))
        column_sql = ", ".join(insert_columns)
        cur.execute(
            f"""
            INSERT INTO baseline_distributions ({column_sql})
            VALUES ({placeholders})
            """,
            [values[column] for column in insert_columns],
        )
        return "inserted"


def log_result(source, metric_key, window_start, window_end, status, errors=0):
    print(
        "Baseline calculation: "
        f"source={source} "
        f"metric_key={metric_key} "
        f"window_start={isoformat_z(window_start)} "
        f"window_end={isoformat_z(window_end)} "
        f"inserted={1 if status == 'inserted' else 0} "
        f"updated={1 if status == 'updated' else 0} "
        f"skipped={1 if status == 'skipped' else 0} "
        f"errors={errors}"
    )


def calculate_for_source(conn, columns, source, days):
    today = datetime.now(timezone.utc).date()
    window_end = utc_midnight(today + timedelta(days=1))
    window_start = window_end - timedelta(days=days)

    if source == "usgs":
        source_name = USGS_SOURCE_NAME
        source_id = get_source_id(conn, source_name)
        metrics = fetch_usgs_daily_metrics(conn, source_id, window_start, window_end)
    elif source == "wikipedia":
        source_name = WIKIPEDIA_SOURCE_NAME
        source_id = get_source_id(conn, source_name)
        wiki_end_date = today - timedelta(days=1)
        window_end = utc_midnight(wiki_end_date)
        window_start = window_end - timedelta(days=days)
        metrics = fetch_wikipedia_daily_metrics(conn, source_id, window_start, window_end)
    else:
        raise ValueError(f"unsupported source: {source}")

    totals = {"inserted": 0, "updated": 0, "skipped": 0, "errors": 0}
    for metric_key, daily_values in metrics.items():
        try:
            payload = build_distribution_payload(
                source_name,
                metric_key,
                window_start,
                window_end,
                daily_values,
            )
            status = save_baseline(
                conn,
                columns,
                source_id,
                metric_key,
                window_start,
                window_end,
                payload,
            )
            totals[status] += 1
            log_result(source, metric_key, window_start, window_end, status)
        except Exception as exc:
            totals["errors"] += 1
            log_result(source, metric_key, window_start, window_end, "skipped", errors=1)
            print(f"Baseline calculation failed for {source}/{metric_key}: {exc}", file=sys.stderr)

    return totals


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Calculate initial World Pulse baselines.")
    parser.add_argument(
        "--source",
        choices=["usgs", "wikipedia", "all"],
        default="all",
        help="Source to calculate baselines for.",
    )
    parser.add_argument("--days", type=int, default=7, help="Baseline lookback window in days.")
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL"),
        help="PostgreSQL connection URL. Defaults to DATABASE_URL.",
    )
    args = parser.parse_args()

    if not args.database_url:
        print("DATABASE_URL is required.", file=sys.stderr)
        return 2

    if args.days <= 0:
        print("--days must be greater than zero.", file=sys.stderr)
        return 2

    sources = ["usgs", "wikipedia"] if args.source == "all" else [args.source]
    totals = {"inserted": 0, "updated": 0, "skipped": 0, "errors": 0}

    with psycopg.connect(args.database_url) as conn:
        columns = table_columns(conn, "baseline_distributions")
        if not columns:
            print("baseline_distributions table was not found.", file=sys.stderr)
            return 1

        for source in sources:
            source_totals = calculate_for_source(conn, columns, source, args.days)
            for key in totals:
                totals[key] += source_totals[key]

        conn.commit()

    print(
        "Baseline calculation completed: "
        f"source={args.source} "
        f"days={args.days} "
        f"inserted={totals['inserted']} "
        f"updated={totals['updated']} "
        f"skipped={totals['skipped']} "
        f"errors={totals['errors']}"
    )
    return 1 if totals["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
