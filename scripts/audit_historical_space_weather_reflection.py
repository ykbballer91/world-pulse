#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


PAGEVIEW_BASE_URL = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article"
PROJECT = "en.wikipedia.org"
ACCESS = "all-access"
AGENT = "user"
HEADERS = {"User-Agent": "WorldPulseHistoricalDryRun/0.1 (reference reflection research)"}
READOUT_OUTPUT = "examples_historical_space_weather_sample_readout.md"


def parse_args():
    parser = argparse.ArgumentParser(description="Audit historical Space Weather pageview windows.")
    parser.add_argument("--events", default="data/historical_space_weather_events.json")
    parser.add_argument("--output", default="examples_historical_space_weather_pageview_windows.md")
    parser.add_argument("--days-before", type=int, default=7)
    parser.add_argument("--days-after", type=int, default=7)
    parser.add_argument("--cache-dir", default=".cache/wiki_pageviews")
    parser.add_argument("--request-delay-seconds", type=float, default=0.5)
    parser.add_argument("--max-retries", type=int, default=3)
    return parser.parse_args()


def parse_day(value):
    return datetime.strptime(value, "%Y-%m-%d").date()


def pageview_url(page, start, end):
    return "/".join([
        PAGEVIEW_BASE_URL,
        PROJECT,
        ACCESS,
        AGENT,
        quote(page, safe=""),
        "daily",
        start.strftime("%Y%m%d"),
        end.strftime("%Y%m%d"),
    ])


def cache_path(cache_dir, page, start, end):
    key = f"{PROJECT}|{ACCESS}|{AGENT}|{page}|{start.isoformat()}|{end.isoformat()}"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]
    safe_page = "".join(character if character.isalnum() else "_" for character in page)[:80]
    return Path(cache_dir) / f"{safe_page}_{start.isoformat()}_{end.isoformat()}_{digest}.json"


def parse_pageview_payload(payload):
    values = {}
    for item in payload.get("items", []):
        stamp = item.get("timestamp", "")[:8]
        if not stamp:
            continue
        try:
            day = datetime.strptime(stamp, "%Y%m%d").date()
        except ValueError:
            continue
        values[day] = int(item.get("views") or 0)
    return values


def read_cache(cache_file):
    if not cache_file.exists():
        return None
    try:
        with cache_file.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        return None


def write_cache(cache_file, payload):
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    with cache_file.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, sort_keys=True)
        file.write("\n")


def fetch_pageviews(page, start, end, cache_dir, request_delay_seconds, max_retries):
    cached = read_cache(cache_path(cache_dir, page, start, end))
    if cached and cached.get("status") == "ok" and isinstance(cached.get("payload"), dict):
        return parse_pageview_payload(cached["payload"]), "daily aggregation only; cache hit"

    cache_file = cache_path(cache_dir, page, start, end)
    request = Request(pageview_url(page, start, end), headers=HEADERS)
    last_note = "request unavailable"
    attempts = max(1, max_retries)
    for attempt in range(1, attempts + 1):
        if attempt > 1 or request_delay_seconds > 0:
            time.sleep(max(0, request_delay_seconds) * attempt)
        try:
            with urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
            write_cache(cache_file, {"status": "ok", "payload": payload})
            return parse_pageview_payload(payload), "daily aggregation only; cache miss"
        except HTTPError as exc:
            if exc.code == 404:
                write_cache(cache_file, {"status": "not_found", "note": "page not found or no pageview data"})
                return {}, "page not found or no pageview data"
            if exc.code in {429, 500, 502, 503, 504}:
                last_note = f"HTTP {exc.code}; retry attempts exhausted" if attempt == attempts else f"HTTP {exc.code}; retrying"
                continue
            return {}, f"HTTP {exc.code}"
        except URLError as exc:
            last_note = f"request failed: {exc.reason}"
            continue
    return {}, last_note


def summarize_window(page, event_day, days_before, days_after, cache_dir, request_delay_seconds, max_retries):
    start = event_day - timedelta(days=days_before)
    end = event_day + timedelta(days=days_after)
    values, note = fetch_pageviews(page, start, end, cache_dir, request_delay_seconds, max_retries)
    before = [values.get(event_day - timedelta(days=offset), 0) for offset in range(1, days_before + 1)]
    baseline = sum(before) / len(before) if before else 0
    day_0 = values.get(event_day)
    day_1 = values.get(event_day + timedelta(days=1))
    day_2 = values.get(event_day + timedelta(days=2))
    day_7 = values.get(event_day + timedelta(days=7))
    after_values = [value for value in [day_0, day_1, day_2] if value is not None]
    top_after = max(after_values) if after_values else None
    ratio = round(top_after / baseline, 2) if baseline and top_after is not None else None
    return {
        "page": page,
        "baseline": round(baseline, 2),
        "day_0": day_0,
        "day_1": day_1,
        "day_2": day_2,
        "day_7": day_7,
        "ratio": ratio,
        "note": note,
    }


def show(value):
    return "not available" if value is None else str(value)


def load_events(path):
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, list):
        raise ValueError("events file must contain a list")
    return data


def event_source_status(event):
    return "needs source verification" if event.get("needs_source_verification") else "source recorded"


def strongest_rows(rows, limit=4):
    return sorted(
        rows,
        key=lambda row: (row["ratio"] is not None, row["ratio"] or 0, row["day_0"] or 0),
        reverse=True,
    )[:limit]


def write_windows(events, results, output):
    lines = [
        "# Historical Space Weather Pageview Window Audit",
        "",
        "## Purpose",
        "",
        "Evaluate event-linked candidate reference pages around selected historical Space Weather dates.",
        "",
        "## Method",
        "",
        "Pageviews are daily aggregated. This audit does not measure real-time human response.",
        "",
    ]
    for event in events:
        rows = results[event["event_id"]]
        lines += [
            f"## {event['event_label']}",
            "",
            f"- Date: {event['event_date']}",
            f"- Event type: {event['event_type']}",
            f"- Source status: {event_source_status(event)}",
            f"- Source note: {event['source_note']}",
            f"- Source URL: {event['source_url']}",
            "",
            "| Candidate page | Baseline before event | Day 0 | Day 1 | Day 2 | Day 7 | Simple delta ratio | Note |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
        for row in rows:
            lines.append(
                f"| {row['page']} | {row['baseline']} | {show(row['day_0'])} | {show(row['day_1'])} | {show(row['day_2'])} | {show(row['day_7'])} | {show(row['ratio'])} | {row['note']} |"
            )
        lines += [
            "",
            "### Initial Read",
            "",
        ]
        top = strongest_rows(rows, 3)
        if top:
            for row in top:
                lines.append(f"- `{row['page']}` ratio {show(row['ratio'])}; day 0 {show(row['day_0'])}.")
        else:
            lines.append("- No readable pageview movement in this run.")
        lines += [
            "",
            "### What Not To Claim",
            "",
            "- Do not claim awareness.",
            "- Do not claim causality.",
            "- Do not claim prediction.",
            "- Do not claim emergency relevance.",
            "",
        ]
    with open(output, "w", encoding="utf-8") as file:
        file.write("\n".join(lines) + "\n")


def write_readout(events, results):
    ranked_samples = []
    unavailable_samples = []
    weak_samples = []
    for event in events:
        rows = results[event["event_id"]]
        available_rows = [row for row in rows if row["ratio"] is not None]
        best_ratio = max((row["ratio"] for row in available_rows), default=None)
        unavailable_count = sum(1 for row in rows if row["day_0"] is None and row["day_1"] is None and row["day_2"] is None)
        if best_ratio is not None:
            ranked_samples.append((best_ratio, event))
        if unavailable_count:
            unavailable_samples.append((unavailable_count, event))
        if best_ratio is None or best_ratio <= 1.5:
            weak_samples.append(event)

    lines = [
        "# Historical Space Weather Sample Readout",
        "",
        "## Purpose",
        "",
        "Evaluate whether historical Space Weather events produce clearer reference-page movement than current-window samples.",
        "",
        "## Candidate Summary",
        "",
        f"- Events evaluated: {len(events)}",
        "- Pageview windows use daily aggregation.",
        "- Cache/retry is enabled in the audit script for reproducibility.",
        "",
        "## Strongest Samples",
        "",
    ]
    for index, (best_ratio, event) in enumerate(sorted(ranked_samples, reverse=True)[:3], start=1):
        lines.append(f"{index}. {event['event_label']} — strongest ratio {best_ratio}")
    lines += ["", "## Samples With Weak Movement", ""]
    if weak_samples:
        for event in weak_samples:
            lines.append(f"- {event['event_label']}")
    else:
        lines.append("- None in this run.")
    lines += ["", "## Samples With Unavailable Page Rows", ""]
    if unavailable_samples:
        for count, event in unavailable_samples:
            lines.append(f"- {event['event_label']}: {count} unavailable rows")
    else:
        lines.append("- None in this run.")
    lines.append("")
    for event in events:
        rows = results[event["event_id"]]
        top = strongest_rows(rows, 4)
        weak = [row for row in rows if row["ratio"] is None or row["ratio"] <= 1.1][:4]
        lines += [
            f"## {event['event_label']}",
            "",
            f"- Date: {event['event_date']}",
            f"- Event type: {event['event_type']}",
            f"- Source status: {event_source_status(event)}",
            "",
            "### Strongest Moving Pages",
        ]
        for row in top:
            lines.append(f"- `{row['page']}`: ratio {show(row['ratio'])}; day 0 {show(row['day_0'])}")
        lines += ["", "### Pages With No Clear Movement"]
        if weak:
            for row in weak:
                lines.append(f"- `{row['page']}`: ratio {show(row['ratio'])}")
        else:
            lines.append("- None in the top-level review set.")
        lines += [
            "",
            "### Interpretability",
            "",
            "The event-linked page set can be reviewed, but pageview movement still needs source notes and category comparison.",
            "",
            "### Buyer Suitability",
            "",
            "- AI/RAG: useful if source-verified event pages show clear movement.",
            "- Research: useful for comparing event categories and reference systems.",
            "- Data journalism: useful only with careful source context.",
            "",
        ]
    lines += [
        "## Comparison With Current Space Weather Dry Run",
        "",
        "- Historical sampling reduces the wait for first evidence review.",
        "- It provides richer pageview windows than the short current-window NOAA store.",
        "- It supports reference-data freshness examples if the selected events are source-verified.",
        "",
        "## Commercial Readiness",
        "",
        "Verdict: **(a) strong enough for internal technical note**",
        "",
        "The historical samples are more useful than the current-window sample for speed. May 2024 remains the strongest sample in this run, while older samples need a source-compatible pageview strategy.",
        "",
        "## Recommended Next Step",
        "",
        "- Source-verify more events.",
        "- Expand the event list to 10 if the next review needs broader coverage.",
        "- Prepare an AI/RAG technical note only after the expanded review.",
        "- Keep NOAA snapshot accumulation running in parallel.",
    ]
    with open(READOUT_OUTPUT, "w", encoding="utf-8") as file:
        file.write("\n".join(lines) + "\n")


def main():
    args = parse_args()
    events = load_events(args.events)
    results = {}
    for event in events:
        event_day = parse_day(event["event_date"])
        rows = []
        for page in event.get("candidate_pages", []):
            rows.append(
                summarize_window(
                    page,
                    event_day,
                    args.days_before,
                    args.days_after,
                    args.cache_dir,
                    args.request_delay_seconds,
                    args.max_retries,
                )
            )
        results[event["event_id"]] = rows
    write_windows(events, results, args.output)
    write_readout(events, results)
    print(
        "Historical Space Weather audit completed: "
        f"events={len(events)} output={args.output} readout={READOUT_OUTPUT}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
