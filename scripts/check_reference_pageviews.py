#!/usr/bin/env python3
import argparse
import os
from datetime import datetime, timedelta, timezone
from statistics import mean
from urllib.parse import quote

import psycopg
import requests
from dotenv import load_dotenv

from link_reality_events_to_reference_pages import (
    KNOWN_PAGE_REPLACEMENTS,
    KNOWN_REGION_PAGE_TITLES,
    candidate_pages_for_event,
    fetch_events,
    isoformat_utc,
    parse_date,
)


PROJECT = "en.wikipedia.org"
ACCESS = "all-access"
AGENT = "WorldPulse/0.1 dry-run reference pageview check"
PAGEVIEW_BASE = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article"
PAGEINFO_URL = "https://en.wikipedia.org/w/api.php"


def parse_dates(value):
    dates = []
    for item in value.split(","):
        item = item.strip()
        if item:
            dates.append(parse_date(item))
    if not dates:
        raise argparse.ArgumentTypeError("--dates must include at least one YYYY-MM-DD value")
    return dates


def compact_title(value):
    return (value or "").replace(" ", "_")


def chunked(items, size):
    for index in range(0, len(items), size):
        yield items[index : index + size]


def fetch_page_existence(session, titles):
    results = {
        compact_title(title): {
            "exists": "unknown",
            "normalized_title": compact_title(title),
        }
        for title in titles
    }

    for batch in chunked(list(results), 40):
        params = {
            "action": "query",
            "format": "json",
            "redirects": "1",
            "prop": "info",
            "titles": "|".join(batch),
        }
        try:
            response = session.get(PAGEINFO_URL, params=params, timeout=20)
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError):
            continue

        query = payload.get("query", {})
        title_map = {title: title for title in batch}
        for item in query.get("normalized", []):
            title_map[compact_title(item.get("from"))] = compact_title(item.get("to"))
        for item in query.get("redirects", []):
            title_map[compact_title(item.get("from"))] = compact_title(item.get("to"))

        pages_by_title = {}
        for page in query.get("pages", {}).values():
            page_title = compact_title(page.get("title"))
            pages_by_title[page_title] = page

        for original in batch:
            resolved = title_map.get(original, original)
            page = pages_by_title.get(resolved)
            if page is None:
                results[original] = {"exists": "unknown", "normalized_title": resolved}
            else:
                results[original] = {
                    "exists": "false" if "missing" in page else "true",
                    "normalized_title": compact_title(page.get("title") or resolved),
                }

    return results


def wikimedia_date(value):
    return value.strftime("%Y%m%d00")


def fetch_pageviews(session, title, start_date, end_date):
    if end_date < start_date:
        return {}

    encoded_title = quote(compact_title(title), safe="")
    url = (
        f"{PAGEVIEW_BASE}/{PROJECT}/{ACCESS}/user/"
        f"{encoded_title}/daily/{wikimedia_date(start_date)}/{wikimedia_date(end_date)}"
    )
    try:
        response = session.get(url, timeout=20)
        if response.status_code == 404:
            return {}
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError):
        return {}

    views_by_date = {}
    for item in payload.get("items", []):
        timestamp = item.get("timestamp", "")
        try:
            date_value = datetime.strptime(timestamp[:8], "%Y%m%d").date()
            views_by_date[date_value] = int(item.get("views", 0))
        except (TypeError, ValueError):
            continue
    return views_by_date


def safe_number(value):
    if value is None:
        return "not available"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def page_rows_for_event(event, existence, pageviews_cache, session, global_start=None, global_end=None):
    event_time = event.get("event_time")
    if event_time is None:
        return []
    if event_time.tzinfo is None:
        event_time = event_time.replace(tzinfo=timezone.utc)
    event_date = event_time.astimezone(timezone.utc).date()
    latest_available_date = datetime.now(timezone.utc).date() - timedelta(days=1)
    range_start = event_date - timedelta(days=7)
    range_end = min(event_date + timedelta(days=7), latest_available_date)
    fetch_start = global_start or range_start
    fetch_end = global_end or range_end
    baseline_dates = [event_date - timedelta(days=offset) for offset in range(7, 0, -1)]
    post_dates = {
        "day_0": event_date,
        "day_1": event_date + timedelta(days=1),
        "day_2": event_date + timedelta(days=2),
        "day_7": event_date + timedelta(days=7),
    }

    candidates = candidate_pages_for_event(event)
    candidate_items = []
    for group in ["core", "context"]:
        for item in candidates[group]:
            candidate_items.append({**item, "group": group})

    rows = []
    for item in candidate_items:
        title = compact_title(item["title"])
        normalized_title = existence.get(title, {}).get("normalized_title", title)
        cache_key = (normalized_title, fetch_start, fetch_end)
        if cache_key not in pageviews_cache:
            pageviews_cache[cache_key] = fetch_pageviews(
                session,
                normalized_title,
                fetch_start,
                fetch_end,
            )
        views_by_date = pageviews_cache[cache_key]

        baseline_values = [views_by_date.get(date_value, 0) for date_value in baseline_dates]
        baseline = float(mean(baseline_values)) if baseline_values else None
        post_values = {}
        for label, date_value in post_dates.items():
            post_values[label] = (
                views_by_date.get(date_value, 0)
                if date_value <= range_end
                else None
            )

        available_post = [
            value for value in [post_values["day_0"], post_values["day_1"], post_values["day_2"]]
            if value is not None
        ]
        post_mean = float(mean(available_post)) if available_post else None
        if baseline is None or baseline == 0 or post_mean is None:
            ratio = None
        else:
            ratio = post_mean / baseline

        rows.append(
            {
                "page_title": title,
                "exists": existence.get(title, {}).get("exists", "unknown"),
                "normalized_title": normalized_title,
                "confidence": item["confidence"],
                "group": item["group"],
                "baseline": baseline,
                "day_0": post_values["day_0"],
                "day_1": post_values["day_1"],
                "day_2": post_values["day_2"],
                "day_7": post_values["day_7"],
                "ratio": ratio,
                "note": "daily aggregation only",
            }
        )
    return rows


def collect_candidate_titles(events_by_date):
    titles = []
    seen = set()
    for events in events_by_date.values():
        for event in events:
            candidates = candidate_pages_for_event(event)
            for group in ["core", "context"]:
                for item in candidates[group]:
                    title = compact_title(item["title"])
                    if title not in seen:
                        seen.add(title)
                        titles.append(title)
    return titles


def reason_category(row):
    title = row["page_title"]
    if title in KNOWN_PAGE_REPLACEMENTS:
        return "likely_title_normalization_issue"
    if title.endswith("_region") and title not in KNOWN_REGION_PAGE_TITLES:
        return "overgenerated_context"
    if row["group"] == "context" and row["confidence"] == "low":
        return "ambiguous_location"
    if row["exists"] == "false":
        return "likely_no_page"
    if row["exists"] == "unknown":
        return "unknown"
    return "exists"


def suggested_replacement(row):
    title = row["page_title"]
    if title in KNOWN_PAGE_REPLACEMENTS:
        return KNOWN_PAGE_REPLACEMENTS[title]
    if title.endswith("_region") and title not in KNOWN_REGION_PAGE_TITLES:
        return title[: -len("_region")]
    return ""


def build_quality_markdown(events_by_date, existence):
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "# Reference Page Candidate Quality Review",
        "",
        f"Generated at: {generated_at}",
        "",
        "## Purpose",
        "",
        "Review candidate reference-page quality before any database storage design.",
        "",
        "## Cleanup Rules Applied",
        "",
        "- Directional modifiers are removed when they break known feature titles.",
        "- Generated `_region` titles are avoided unless explicitly known.",
        "- Distance and direction fragments are trimmed before location parsing.",
        "- Low-confidence town candidates are kept only when explicitly allowed in this dry run.",
        "",
        "## Candidate Quality Rows",
        "",
        "| Candidate page title | Source event | Exists | Reason category | Suggested replacement |",
        "| --- | --- | --- | --- | --- |",
    ]

    false_count = 0
    total_count = 0
    for events in events_by_date.values():
        for event in events:
            candidates = candidate_pages_for_event(event)
            for group in ["core", "context"]:
                for item in candidates[group]:
                    title = compact_title(item["title"])
                    row = {
                        "page_title": title,
                        "exists": existence.get(title, {}).get("exists", "unknown"),
                        "group": group,
                        "confidence": item["confidence"],
                    }
                    total_count += 1
                    if row["exists"] == "false":
                        false_count += 1
                    lines.append(
                        "| "
                        + " | ".join(
                            [
                                row["page_title"],
                                event["title"].replace("|", "/"),
                                row["exists"],
                                reason_category(row),
                                suggested_replacement(row) or "none",
                            ]
                        )
                        + " |"
                    )

    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Candidate rows reviewed: {total_count}",
            f"- `exists=false` rows after cleanup: {false_count}",
            "- Remaining low-confidence rows should be manually reviewed before database storage.",
            "",
        ]
    )
    return "\n".join(lines)


def markdown_table(rows):
    lines = [
        "| Page | Group | Exists | Normalized title | Confidence | Baseline before event | Day 0 | Day 1 | Day 2 | Day 7 | Simple delta ratio | Note |",
        "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["page_title"],
                    row["group"],
                    row["exists"],
                    row["normalized_title"],
                    row["confidence"],
                    safe_number(row["baseline"]),
                    safe_number(row["day_0"]),
                    safe_number(row["day_1"]),
                    safe_number(row["day_2"]),
                    safe_number(row["day_7"]),
                    safe_number(row["ratio"]),
                    row["note"],
                ]
            )
            + " |"
        )
    return lines


def format_event_section(event, rows):
    lines = [
        f"### Reality event",
        "",
        f"- Title: {event['title']}",
        f"- Event time: {isoformat_utc(event.get('event_time'))}",
        f"- Category: {event.get('category')}",
        f"- Event type: {event.get('event_type')}",
        f"- Magnitude: {safe_number(event.get('magnitude_value'))}",
        f"- Location phrase: {event.get('location_label') or 'unknown location'}",
        "",
        "### Candidate pages checked",
        "",
    ]
    for row in rows:
        lines.append(
            f"- {row['page_title']} ({row['group']}, exists={row['exists']}, confidence={row['confidence']})"
        )
    lines.extend(
        [
            "",
            "### Pageview window",
            "",
            *markdown_table(rows),
            "",
            "### Initial read",
            "",
            "Daily pageview movement is measurable for pages with available data. This dry run does not infer event-specific reflection.",
            "",
            "### What not to claim",
            "",
            "- Do not claim awareness.",
            "- Do not claim emergency relevance.",
            "- Do not claim prediction.",
            "- Do not treat low or absent candidate-page activity as absence of public attention.",
            "",
        ]
    )
    return lines


def global_pageview_window(events_by_date):
    event_dates = []
    for events in events_by_date.values():
        for event in events:
            event_time = event.get("event_time")
            if event_time is None:
                continue
            if event_time.tzinfo is None:
                event_time = event_time.replace(tzinfo=timezone.utc)
            event_dates.append(event_time.astimezone(timezone.utc).date())
    if not event_dates:
        return None, None
    latest_available_date = datetime.now(timezone.utc).date() - timedelta(days=1)
    return (
        min(event_dates) - timedelta(days=7),
        min(max(event_dates) + timedelta(days=7), latest_available_date),
    )


def build_markdown(events_by_date, existence, pageviews_cache, session):
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    global_start, global_end = global_pageview_window(events_by_date)
    lines = [
        "# Reference Pageview Window Dry Run",
        "",
        f"Generated at: {generated_at}",
        "",
        "## Purpose",
        "",
        "Evaluate whether event-linked candidate pages show measurable reference activity after selected reality events.",
        "",
        "## Method",
        "",
        "Candidate pages are heuristic. Pageviews are daily aggregated. This does not measure real-time human awareness.",
        "",
    ]

    total_rows = 0
    existing_true = 0
    for date_text, events in events_by_date.items():
        lines.extend([f"## Candidate date: {date_text}", ""])
        if not events:
            lines.extend(["No selected earthquake events found for this date.", ""])
            continue
        for event in events:
            rows = page_rows_for_event(
                event,
                existence,
                pageviews_cache,
                session,
                global_start=global_start,
                global_end=global_end,
            )
            total_rows += len(rows)
            existing_true += sum(1 for row in rows if row["exists"] == "true")
            lines.extend(format_event_section(event, rows))

    lines.extend(
        [
            "## Overall assessment",
            "",
            f"- Page existence checks returned `true` for {existing_true} of {total_rows} checked event-page rows.",
            "- Pageview windows can be generated for candidate pages where data is available.",
            "- This is closer to a commercial sample because it narrows reflection checks from date-level aggregates to event-linked reference pages.",
            "- More precise entity linking is still needed before storing these measurements or using them in scored outputs.",
            "- Next step: page existence review, title cleanup, and pageview-window measurement design.",
            "",
        ]
    )
    return "\n".join(lines)


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Dry-run page existence and pageview windows for event-linked reference pages."
    )
    parser.add_argument("--dates", type=parse_dates, required=True, help="Comma-separated YYYY-MM-DD dates.")
    parser.add_argument("--limit", type=int, default=3, help="Maximum events per date.")
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL"),
        help="PostgreSQL connection URL. Defaults to DATABASE_URL.",
    )
    parser.add_argument(
        "--output",
        default="examples_reference_pageview_windows.md",
        help="Markdown output path.",
    )
    parser.add_argument(
        "--quality-output",
        default="examples_reference_page_quality.md",
        help="Candidate quality markdown output path.",
    )
    args = parser.parse_args()

    if not args.database_url:
        print("DATABASE_URL is required.")
        return 2
    if args.limit <= 0:
        print("--limit must be greater than zero.")
        return 2

    events_by_date = {}
    with psycopg.connect(args.database_url) as conn:
        for target_date in args.dates:
            events_by_date[target_date.isoformat()] = fetch_events(conn, target_date, args.limit)

    session = requests.Session()
    session.headers.update({"User-Agent": AGENT})

    candidate_titles = collect_candidate_titles(events_by_date)
    existence = fetch_page_existence(session, candidate_titles)
    pageviews_cache = {}
    markdown = build_markdown(events_by_date, existence, pageviews_cache, session)
    quality_markdown = build_quality_markdown(events_by_date, existence)

    with open(args.output, "w", encoding="utf-8") as file:
        file.write(markdown)
    if args.quality_output:
        with open(args.quality_output, "w", encoding="utf-8") as file:
            file.write(quality_markdown)

    total_events = sum(len(events) for events in events_by_date.values())
    print(
        "Reference pageview dry run completed: "
        f"dates={len(events_by_date)} events={total_events} "
        f"candidate_pages={len(candidate_titles)} output={args.output} "
        f"quality_output={args.quality_output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
