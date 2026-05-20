#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys
import time
from datetime import datetime
from urllib.parse import urlparse

import psycopg
from dotenv import load_dotenv


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--date must use YYYY-MM-DD format") from exc


def script_path(name):
    return os.path.join(ROOT_DIR, "scripts", name)


def command_text(command):
    masked = []
    mask_next = False
    for part in command:
        if mask_next:
            masked.append("***")
            mask_next = False
            continue
        masked.append(part)
        if part == "--database-url":
            mask_next = True
    return " ".join(masked)


def database_url_args(database_url):
    return ["--database-url", database_url]


def database_url_host(database_url):
    parsed = urlparse(database_url)
    return parsed.hostname


def validate_database_url(database_url):
    host = database_url_host(database_url)
    if not host:
        raise ValueError("DATABASE_URL host could not be determined")

    print(f"DATABASE_URL host: {host}")
    if host in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("DATABASE_URL points to a local database host")


def run_step(name, command, critical=True, warnings=None):
    started = time.monotonic()
    print(f"Step started: name={name} command={command_text(command)}")
    child_env = os.environ.copy()
    print(
        "DATABASE_URL will be passed to subprocess: "
        f"{'yes' if child_env.get('DATABASE_URL') else 'no'}"
    )
    print(f"DATABASE_URL passed via CLI: {'yes' if '--database-url' in command else 'no'}")
    result = subprocess.run(
        command,
        cwd=ROOT_DIR,
        check=False,
        text=True,
        env=child_env,
    )
    elapsed = time.monotonic() - started
    status = "success" if result.returncode == 0 else ("failed" if critical else "warning")
    print(f"Step finished: name={name} status={status} elapsed_seconds={elapsed:.2f}")
    if result.returncode != 0:
        if not critical:
            warning = f"{name} failed"
            print(f"{warning} but daily build will continue.")
            if warnings is not None:
                warnings.append(warning)
            return False
        raise RuntimeError(f"step failed: {name}")
    return True


def latest_anomaly_date(database_url):
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT event_time::date
                FROM normalized_events
                WHERE anomaly_score IS NOT NULL
                  AND event_time IS NOT NULL
                ORDER BY event_time DESC
                LIMIT 1
                """
            )
            row = cur.fetchone()
            if row is None:
                raise ValueError("no normalized_events with anomaly_score were found")
            return row[0]


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Run the World Pulse daily build.")
    parser.add_argument(
        "--date",
        type=parse_date,
        default=None,
        help="Target date in YYYY-MM-DD format.",
    )
    parser.add_argument("--days", type=int, default=30, help="Backfill and baseline lookback days.")
    parser.add_argument("--skip-ingest", action="store_true", help="Skip external API ingestion.")
    parser.add_argument("--skip-backfill", action="store_true", help="Skip backfill steps.")
    parser.add_argument("--skip-image", action="store_true", help="Skip share image generation.")
    parser.add_argument("--skip-x-text", action="store_true", help="Skip X post text generation.")
    parser.add_argument(
        "--database-url",
        default=None,
        help="PostgreSQL connection URL. Defaults to DATABASE_URL.",
    )
    args = parser.parse_args()

    resolved_database_url = args.database_url or os.environ.get("DATABASE_URL")
    if not resolved_database_url:
        print("DATABASE_URL is required.", file=sys.stderr)
        return 2

    os.environ["DATABASE_URL"] = resolved_database_url
    if os.environ.get("DATABASE_URL"):
        print("DATABASE_URL available for daily build")
    else:
        print("DATABASE_URL is not available for daily build")
        return 1

    try:
        validate_database_url(resolved_database_url)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    db_args = database_url_args(resolved_database_url)

    if args.days <= 0:
        print("--days must be greater than zero.", file=sys.stderr)
        return 2

    warnings = []

    try:
        if not args.skip_ingest:
            run_step(
                "USGS ingest",
                [
                    sys.executable,
                    script_path("ingest_usgs_earthquakes.py"),
                    "--hours",
                    "168",
                    "--min-magnitude",
                    "4",
                    *db_args,
                ],
            )
            run_step(
                "NOAA SWPC Kp ingest",
                [
                    sys.executable,
                    script_path("ingest_noaa_swpc.py"),
                    "--dataset",
                    "kp",
                    *db_args,
                ],
            )
            run_step(
                "NOAA SWPC X-ray ingest",
                [
                    sys.executable,
                    script_path("ingest_noaa_swpc.py"),
                    "--dataset",
                    "xray",
                    *db_args,
                ],
            )
            run_step(
                "Open Notify ingest",
                [
                    sys.executable,
                    script_path("ingest_open_notify.py"),
                    "--dataset",
                    "all",
                    *db_args,
                ],
                critical=False,
                warnings=warnings,
            )
            run_step(
                "Cloudflare Radar ingest",
                [
                    sys.executable,
                    script_path("ingest_cloudflare_radar.py"),
                    "--dataset",
                    "outages",
                    *db_args,
                ],
                critical=False,
                warnings=warnings,
            )

        if not args.skip_backfill:
            run_step(
                "Wikipedia backfill",
                [
                    sys.executable,
                    script_path("backfill_day2_sources.py"),
                    "--source",
                    "wikipedia",
                    "--days",
                    str(args.days),
                    *db_args,
                ],
            )
            run_step(
                "USGS backfill",
                [
                    sys.executable,
                    script_path("backfill_day2_sources.py"),
                    "--source",
                    "usgs",
                    "--days",
                    str(args.days),
                    *db_args,
                ],
            )

        run_step(
            "Baseline calculation",
            [
                sys.executable,
                script_path("calculate_baseline_distributions.py"),
                "--source",
                "all",
                "--days",
                str(args.days),
                *db_args,
            ],
        )
        run_step(
            "Normalized events",
            [
                sys.executable,
                script_path("generate_normalized_events.py"),
                "--source",
                "all",
                *db_args,
            ],
        )

        target_date = args.date or latest_anomaly_date(resolved_database_url)
        target_date_text = target_date.isoformat()
        print(f"Daily build target_date={target_date_text}")

        run_step(
            "Weirdness score",
            [
                sys.executable,
                script_path("calculate_weirdness_score.py"),
                "--date",
                target_date_text,
                *db_args,
            ],
        )
        run_step(
            "Display payload",
            [
                sys.executable,
                script_path("generate_display_payload.py"),
                "--date",
                target_date_text,
                *db_args,
            ],
        )
        run_step(
            "Display JSON export",
            [
                sys.executable,
                script_path("export_display_payload_json.py"),
                "--date",
                target_date_text,
                *db_args,
            ],
        )

        if not args.skip_image:
            run_step(
                "Share image",
                [
                    sys.executable,
                    script_path("generate_share_image.py"),
                    "--date",
                    target_date_text,
                    *db_args,
                ],
            )

        if not args.skip_x_text:
            run_step(
                "X post text",
                [
                    sys.executable,
                    script_path("generate_x_post_text.py"),
                    "--date",
                    target_date_text,
                    *db_args,
                ],
            )

    except Exception as exc:
        print(f"World Pulse daily build failed: {exc}", file=sys.stderr)
        return 1

    print(
        "\nWorld Pulse daily build completed.\n\n"
        f"target_date: {target_date_text}\n"
        "display_json: public/display/latest.json\n"
        "share_image_png: public/share/world-pulse-latest.png\n"
        "share_image_jpg: public/share/world-pulse-latest.jpg\n"
        "x_post_text: public/share/world-pulse-latest.txt\n"
        "local_preview: http://localhost:8080/"
    )
    if warnings:
        print("\nwarnings:")
        for warning in warnings:
            print(f"- {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
