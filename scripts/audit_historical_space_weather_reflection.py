#!/usr/bin/env python3
import argparse
import json
import os
from datetime import datetime, timedelta
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


def fetch_pageviews(page, start, end):
    request = Request(pageview_url(page, start, end), headers=HEADERS)
    try:
        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 404:
            return {}, "page not found or no pageview data"
        if exc.code == 429:
            return {}, "rate limited by Wikimedia API"
        return {}, f"HTTP {exc.code}"
    except URLError as exc:
        return {}, f"request failed: {exc.reason}"

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
    return values, "daily aggregation only"


def summarize_window(page, event_day, days_before, days_after):
    start = event_day - timedelta(days=days_before)
    end = event_day + timedelta(days=days_after)
    values, note = fetch_pageviews(page, start, end)
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
    lines = [
        "# Historical Space Weather Sample Readout",
        "",
        "## Purpose",
        "",
        "Evaluate whether historical Space Weather events produce clearer reference-page movement than current-window samples.",
        "",
        "## Candidate Summary",
        "",
    ]
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
        "Verdict: **(b) promising but needs more source-verified events**",
        "",
        "The historical samples are more useful than the current-window sample for speed, but the event set should expand before buyer-facing use.",
        "",
        "## Recommended Next Step",
        "",
        "- Source-verify more events.",
        "- Expand the event list to 10.",
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
            rows.append(summarize_window(page, event_day, args.days_before, args.days_after))
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
