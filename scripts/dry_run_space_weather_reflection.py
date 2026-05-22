#!/usr/bin/env python3
import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from urllib.parse import quote

import psycopg
import requests
from dotenv import load_dotenv


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOAA_SOURCE_NAME = "NOAA SWPC"
REGISTRY_PATH = os.path.join(ROOT_DIR, "reference_candidate_registry_space_weather.json")
DATA_AVAILABILITY_OUTPUT = "examples_space_weather_data_availability.md"
PAGEVIEW_OUTPUT = "examples_space_weather_pageview_windows.md"
READOUT_OUTPUT = "examples_space_weather_sample_readout.md"
PAGEVIEW_PROJECT = "en.wikipedia.org"
PAGEVIEW_AGENT = "user"
PAGEVIEW_ACCESS = "all-access"
PAGEVIEW_BASE_URL = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article"
HEADERS = {"User-Agent": "WorldPulseDryRun/0.1 (reference reflection research)"}
M_CLASS_FLUX = 1e-5
X_CLASS_FLUX = 1e-4


def parse_args():
    parser = argparse.ArgumentParser(description="Dry-run Space Weather Reality-Reflection checks.")
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--kp-threshold", type=float, default=5.0)
    parser.add_argument("--xray-threshold", default="M")
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"))
    parser.add_argument("--output", default="examples_space_weather_entity_linking_dryrun.md")
    return parser.parse_args()


def parse_time(value):
    if not value:
        return None
    if isinstance(value, str) and value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def iso_minute(value):
    if value is None:
        return "unknown"
    return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def ymd(value):
    return value.astimezone(timezone.utc).strftime("%Y%m%d")


def markdown_date(value):
    return value.astimezone(timezone.utc).date().isoformat()


def fetch_noaa_raw(conn, days):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT ro.id, ro.observed_at, ro.raw_payload
            FROM raw_observations ro
            JOIN sources s ON s.id = ro.source_id
            WHERE s.name = %s
              AND ro.observed_at >= %s
            ORDER BY ro.observed_at
            """,
            (NOAA_SOURCE_NAME, since),
        )
        return cur.fetchall()


def collect_availability(rows):
    stats = {}
    for _raw_id, observed_at, payload in rows:
        dataset = payload.get("dataset") or "unknown"
        records = payload.get("records") or []
        item = stats.setdefault(
            dataset,
            {
                "raw_count": 0,
                "record_count": 0,
                "raw_earliest": None,
                "raw_latest": None,
                "record_earliest": None,
                "record_latest": None,
                "max_kp": None,
                "max_flux": None,
            },
        )
        item["raw_count"] += 1
        item["record_count"] += len(records)
        item["raw_earliest"] = observed_at if item["raw_earliest"] is None or observed_at < item["raw_earliest"] else item["raw_earliest"]
        item["raw_latest"] = observed_at if item["raw_latest"] is None or observed_at > item["raw_latest"] else item["raw_latest"]
        for record in records:
            record_time = parse_time(record.get("time_tag"))
            if record_time is not None:
                item["record_earliest"] = record_time if item["record_earliest"] is None or record_time < item["record_earliest"] else item["record_earliest"]
                item["record_latest"] = record_time if item["record_latest"] is None or record_time > item["record_latest"] else item["record_latest"]
            if dataset == "kp":
                value = record.get("estimated_kp", record.get("kp_index"))
                try:
                    value = float(value)
                except (TypeError, ValueError):
                    continue
                item["max_kp"] = value if item["max_kp"] is None or value > item["max_kp"] else item["max_kp"]
            elif dataset == "xray" and record.get("energy") == "0.1-0.8nm":
                try:
                    value = float(record.get("flux"))
                except (TypeError, ValueError):
                    continue
                item["max_flux"] = value if item["max_flux"] is None or value > item["max_flux"] else item["max_flux"]
    return stats


def usable_days(item):
    start = item.get("record_earliest")
    end = item.get("record_latest")
    if start is None or end is None:
        return 0.0
    return round((end - start).total_seconds() / 86400, 2)


def write_availability(stats, requested_days):
    lines = [
        "# Space Weather Data Availability",
        "",
        "## Purpose",
        "",
        "Audit stored NOAA SWPC data before Space Weather dry-run analysis.",
        "",
        f"Requested lookback: {requested_days} days",
        "",
        "## Stored Data",
        "",
        "| Dataset | Raw rows | Records | Earliest raw observed_at | Latest raw observed_at | Earliest record time | Latest record time | Usable days | Coverage note |",
        "| --- | ---: | ---: | --- | --- | --- | --- | ---: | --- |",
    ]
    for dataset in sorted(stats):
        item = stats[dataset]
        days = usable_days(item)
        note = "true 90-day coverage" if days >= 89 else "provider current window only"
        lines.append(
            f"| {dataset} | {item['raw_count']} | {item['record_count']} | "
            f"{iso_minute(item['raw_earliest'])} | {iso_minute(item['raw_latest'])} | "
            f"{iso_minute(item['record_earliest'])} | {iso_minute(item['record_latest'])} | {days} | {note} |"
        )
    lines += [
        "",
        "## Summary",
        "",
        "Stored NOAA SWPC data does not currently provide a full 90-day historical record. The dry-run uses the available provider current windows only.",
    ]
    with open(os.path.join(ROOT_DIR, DATA_AVAILABILITY_OUTPUT), "w", encoding="utf-8") as file:
        file.write("\n".join(lines) + "\n")


def threshold_flux(threshold):
    value = str(threshold).strip().upper()
    if value == "M":
        return M_CLASS_FLUX
    if value == "X":
        return X_CLASS_FLUX
    return float(value)


def flare_class(flux):
    if flux >= X_CLASS_FLUX:
        return f"X{flux / X_CLASS_FLUX:.1f}"
    if flux >= M_CLASS_FLUX:
        return f"M{flux / M_CLASS_FLUX:.1f}"
    return f"C{flux / 1e-6:.1f}"


def load_registry():
    with open(REGISTRY_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)
    return [entry for entry in data if isinstance(entry, dict)]


def registry_candidates(event_type):
    grouped = defaultdict(list)
    for entry in load_registry():
        if entry.get("event_type") != event_type:
            continue
        grouped[entry.get("candidate_group", "context")].append(entry)
    return grouped


def unique_xray_records(rows):
    by_time = {}
    for _raw_id, _observed_at, payload in rows:
        if payload.get("dataset") != "xray":
            continue
        for record in payload.get("records") or []:
            if record.get("energy") != "0.1-0.8nm":
                continue
            event_time = parse_time(record.get("time_tag"))
            if event_time is None:
                continue
            try:
                flux = float(record.get("flux"))
            except (TypeError, ValueError):
                continue
            current = by_time.get(event_time)
            if current is None or flux > current["flux"]:
                by_time[event_time] = {"event_time": event_time, "flux": flux, "record": record}
    return [by_time[key] for key in sorted(by_time)]


def unique_kp_records(rows):
    by_time = {}
    for _raw_id, _observed_at, payload in rows:
        if payload.get("dataset") != "kp":
            continue
        for record in payload.get("records") or []:
            event_time = parse_time(record.get("time_tag"))
            if event_time is None:
                continue
            value = record.get("estimated_kp", record.get("kp_index"))
            try:
                kp_value = float(value)
            except (TypeError, ValueError):
                continue
            current = by_time.get(event_time)
            if current is None or kp_value > current["kp"]:
                by_time[event_time] = {"event_time": event_time, "kp": kp_value, "record": record}
    return [by_time[key] for key in sorted(by_time)]


def extract_xray_events(rows, threshold):
    records = [record for record in unique_xray_records(rows) if record["flux"] >= threshold]
    groups = []
    current = []
    for record in records:
        if not current:
            current = [record]
            continue
        gap = (record["event_time"] - current[-1]["event_time"]).total_seconds()
        if gap <= 600:
            current.append(record)
        else:
            groups.append(current)
            current = [record]
    if current:
        groups.append(current)

    events = []
    for group in groups:
        peak = max(group, key=lambda item: item["flux"])
        events.append(
            {
                "event_time": peak["event_time"],
                "event_type": "solar_flare",
                "observed_value": flare_class(peak["flux"]),
                "numeric_value": peak["flux"],
                "source": "NOAA SWPC X-ray",
                "strength": "stronger solar flare candidate" if peak["flux"] >= X_CLASS_FLUX else "solar flare candidate",
            }
        )
    return sorted(events, key=lambda item: item["numeric_value"], reverse=True)


def extract_kp_events(rows, threshold):
    records = [record for record in unique_kp_records(rows) if record["kp"] >= threshold]
    groups = []
    current = []
    for record in records:
        if not current:
            current = [record]
            continue
        gap = (record["event_time"] - current[-1]["event_time"]).total_seconds()
        if gap <= 1800:
            current.append(record)
        else:
            groups.append(current)
            current = [record]
    if current:
        groups.append(current)

    events = []
    for group in groups:
        peak = max(group, key=lambda item: item["kp"])
        events.append(
            {
                "event_time": peak["event_time"],
                "event_type": "geomagnetic_storm",
                "observed_value": f"Kp {peak['kp']:.2f}",
                "numeric_value": peak["kp"],
                "source": "NOAA SWPC Kp",
                "strength": "stronger geomagnetic candidate" if peak["kp"] >= 7 else "geomagnetic event candidate",
            }
        )
    return sorted(events, key=lambda item: item["numeric_value"], reverse=True)


def pageview_url(page, start, end):
    return "/".join(
        [
            PAGEVIEW_BASE_URL,
            PAGEVIEW_PROJECT,
            PAGEVIEW_ACCESS,
            PAGEVIEW_AGENT,
            quote(page, safe=""),
            "daily",
            start,
            end,
        ]
    )


def fetch_pageviews(page, start_date, end_date):
    start = start_date.strftime("%Y%m%d")
    end = end_date.strftime("%Y%m%d")
    response = requests.get(pageview_url(page, start, end), headers=HEADERS, timeout=30)
    if response.status_code == 404:
        return [], "page not found or no pageview data"
    if response.status_code == 429:
        return [], "rate limited by Wikimedia API"
    if response.status_code >= 400:
        return [], f"HTTP {response.status_code}"
    return response.json().get("items", []), "daily aggregation only"


def pageview_window(page, event_day):
    start = event_day - timedelta(days=7)
    end = event_day + timedelta(days=7)
    items, note = fetch_pageviews(page, start, end)
    views = {}
    for item in items:
        stamp = item.get("timestamp", "")[:8]
        if not stamp:
            continue
        try:
            day = datetime.strptime(stamp, "%Y%m%d").date()
        except ValueError:
            continue
        views[day] = int(item.get("views") or 0)
    before = [views.get(event_day - timedelta(days=offset), 0) for offset in range(1, 8)]
    baseline = sum(before) / len(before) if before else 0
    day_0 = views.get(event_day)
    day_1 = views.get(event_day + timedelta(days=1))
    day_2 = views.get(event_day + timedelta(days=2))
    day_7 = views.get(event_day + timedelta(days=7))
    values = [value for value in [day_0, day_1, day_2] if value is not None]
    top_after = max(values) if values else None
    ratio = None
    if baseline and top_after is not None:
        ratio = round(top_after / baseline, 2)
    return {
        "baseline": round(baseline, 2),
        "day_0": day_0,
        "day_1": day_1,
        "day_2": day_2,
        "day_7": day_7,
        "ratio": ratio,
        "note": note,
    }


def selected_candidate_pages(event):
    grouped = registry_candidates(event["event_type"])
    pages = []
    for group in ["core", "extended", "context", "historical_reference"]:
        for entry in grouped.get(group, []):
            page = entry["candidate_page"]
            if page not in {item["candidate_page"] for item in pages}:
                pages.append(entry)
    return pages


def write_entity_dryrun(path, events, stats, requested_days):
    lines = [
        "# Space Weather Entity Linking Dry Run",
        "",
        "## Purpose",
        "",
        "Test whether stored NOAA SWPC observations can produce event-level candidate reference pages for Space Weather reflection checks.",
        "",
        "## Usable Data Range",
        "",
        f"Requested lookback: {requested_days} days",
        "",
    ]
    for dataset in sorted(stats):
        item = stats[dataset]
        lines.append(f"- {dataset}: {iso_minute(item['record_earliest'])} to {iso_minute(item['record_latest'])}; usable days {usable_days(item)}")
    lines += ["", "## Candidate Events", ""]
    if not events:
        lines += ["No Space Weather candidate events were extracted from the available stored data.", ""]
    for event in events:
        lines += [
            f"## Event: {event['event_type']} at {iso_minute(event['event_time'])}",
            "",
            f"- Event time: {iso_minute(event['event_time'])}",
            f"- Event type: {event['event_type']}",
            f"- Observed value: {event['observed_value']}",
            f"- Source: {event['source']}",
            f"- Candidate class: {event['strength']}",
            "",
            "### Candidate Reference Pages",
        ]
        for entry in selected_candidate_pages(event):
            lines.append(f"- {entry['candidate_page']} ({entry['candidate_group']}; {entry['confidence']}; {entry['review_status']})")
        lines += [
            "",
            "### What Still Needs To Be Measured",
            "- Pageview activity in day_0 / day_1 / day_2 / day_7 windows.",
            "- Whether page movement is event-specific or background traffic.",
            "- Whether the candidate page set is too broad for a buyer-facing sample.",
            "",
            "### What Not To Claim",
            "- Do not claim awareness.",
            "- Do not claim causality.",
            "- Do not claim prediction.",
            "- Do not claim emergency relevance.",
            "",
        ]
    with open(path, "w", encoding="utf-8") as file:
        file.write("\n".join(lines) + "\n")


def write_pageview_windows(events):
    lines = [
        "# Space Weather Pageview Window Dry Run",
        "",
        "## Purpose",
        "",
        "Measure daily pageview windows for candidate Space Weather reference pages.",
        "",
        "## Method",
        "",
        "Pageviews are daily aggregated. This does not measure real-time human response.",
        "",
    ]
    summaries = []
    for event in events:
        lines += [
            f"## Event: {event['event_type']} at {iso_minute(event['event_time'])}",
            "",
            f"- Observed value: {event['observed_value']}",
            f"- Source: {event['source']}",
            "",
            "| Page | Group | Confidence | Review status | Baseline 7d | Day 0 | Day 1 | Day 2 | Day 7 | Simple delta ratio | Note |",
            "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
        for entry in selected_candidate_pages(event):
            window = pageview_window(entry["candidate_page"], event["event_time"].date())
            summaries.append({"event": event, "entry": entry, "window": window})
            def show(value):
                return "not available" if value is None else str(value)
            lines.append(
                f"| {entry['candidate_page']} | {entry['candidate_group']} | {entry['confidence']} | {entry['review_status']} | "
                f"{window['baseline']} | {show(window['day_0'])} | {show(window['day_1'])} | {show(window['day_2'])} | {show(window['day_7'])} | {show(window['ratio'])} | {window['note']} |"
            )
        lines.append("")
    with open(os.path.join(ROOT_DIR, PAGEVIEW_OUTPUT), "w", encoding="utf-8") as file:
        file.write("\n".join(lines) + "\n")
    return summaries


def best_summary_for_event(event, summaries):
    rows = [item for item in summaries if item["event"] is event]
    rows.sort(key=lambda item: (item["window"]["ratio"] is not None, item["window"]["ratio"] or 0), reverse=True)
    return rows[:4]


def write_readout(events, stats, summaries):
    lines = [
        "# Space Weather Reflection Sample Readout",
        "",
        "## Purpose",
        "",
        "Evaluate whether Space Weather produces clearer event-to-reference page movement than earthquake samples.",
        "",
        "## Data Availability",
        "",
    ]
    for dataset in sorted(stats):
        item = stats[dataset]
        lines.append(f"- {dataset}: usable days {usable_days(item)}; {iso_minute(item['record_earliest'])} to {iso_minute(item['record_latest'])}")
    lines += ["", "## Candidate Events", ""]
    if not events:
        lines += ["No candidate events were available in the stored NOAA SWPC window.", ""]
    for index, event in enumerate(events[:3], 1):
        rows = best_summary_for_event(event, summaries)
        lines += [
            f"## Candidate {index}: {event['event_type']} / {markdown_date(event['event_time'])}",
            "",
            "### Reality Event",
            "",
            f"- Event time: {iso_minute(event['event_time'])}",
            f"- Observed value: {event['observed_value']}",
            f"- Source: {event['source']}",
            "",
            "### Candidate Pages",
        ]
        for entry in selected_candidate_pages(event):
            lines.append(f"- {entry['candidate_page']} ({entry['candidate_group']})")
        lines += ["", "### Pageview Movement Summary", ""]
        for row in rows:
            window = row["window"]
            lines.append(f"- `{row['entry']['candidate_page']}`: baseline {window['baseline']}, day 0 {window['day_0']}, simple delta ratio {window['ratio']}")
        lines += [
            "",
            "### Why It May Matter",
            "",
            "This sample tests whether a compact Space Weather page set produces clearer reference movement than place-dependent earthquake samples.",
            "",
            "### What We Can Say",
            "",
            "- Candidate reference pages can be generated from a reviewed registry.",
            "- Daily pageview windows can be measured for these pages.",
            "- The result can be compared with earthquake Phase 2 samples.",
            "",
            "### What We Cannot Say",
            "",
            "- We cannot claim causality.",
            "- We cannot claim public awareness.",
            "- We cannot claim prediction.",
            "- We cannot claim emergency relevance.",
            "",
            "### Buyer Suitability",
            "",
            "- AI/RAG: useful for reference-data freshness review if page movement is visible.",
            "- Insurance/research: useful only as a research signal, not as an action trigger.",
            "- Data journalism: useful if paired with careful source notes.",
            "- Academic/policy: useful for comparing event categories.",
            "",
        ]
    lines += [
        "## Comparison With Earthquake",
        "",
        "- Candidate pages are cleaner because Space Weather uses a compact domain vocabulary.",
        "- Location parsing is much less central than in earthquake samples.",
        "- Pageview movement may be easier to review if the candidate event is strong enough.",
        "- The stored data window is short, so evidence remains provisional.",
        "",
        "## Commercial Readiness",
        "",
        "Verdict: **(b) promising but needs more evidence**",
        "",
        "The category looks structurally cleaner than earthquake, but the stored NOAA SWPC data window is short and Kp candidates are absent in the current data. More stored history or another current-window sample is needed before buyer-facing use.",
    ]
    with open(os.path.join(ROOT_DIR, READOUT_OUTPUT), "w", encoding="utf-8") as file:
        file.write("\n".join(lines) + "\n")


def main():
    load_dotenv()
    args = parse_args()
    if not args.database_url:
        print("DATABASE_URL is required.", file=sys.stderr)
        return 2

    flux_threshold = threshold_flux(args.xray_threshold)
    with psycopg.connect(args.database_url) as conn:
        rows = fetch_noaa_raw(conn, args.days)
    stats = collect_availability(rows)
    write_availability(stats, args.days)

    kp_events = extract_kp_events(rows, args.kp_threshold)
    xray_events = extract_xray_events(rows, flux_threshold)
    events = sorted(kp_events + xray_events, key=lambda item: item["numeric_value"], reverse=True)[:3]
    if len(events) < 3:
        events = (xray_events + kp_events)[:3]

    write_entity_dryrun(os.path.join(ROOT_DIR, args.output), events, stats, args.days)
    summaries = write_pageview_windows(events)
    write_readout(events, stats, summaries)

    print(
        "Space Weather dry run completed: "
        f"raw_rows={len(rows)} kp_events={len(kp_events)} xray_events={len(xray_events)} "
        f"selected_events={len(events)} output={args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
