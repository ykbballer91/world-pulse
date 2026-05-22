#!/usr/bin/env python3
import argparse
import json
import os
import re
from datetime import datetime, timedelta, timezone

import psycopg
from dotenv import load_dotenv


CORE_EARTHQUAKE_PAGES = ["Earthquake", "Seismology", "Seismic_wave"]
TSUNAMI_PAGE = "Tsunami"
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_REGISTRY_PATH = os.path.join(ROOT_DIR, "reference_candidate_registry.json")

KNOWN_PAGE_REPLACEMENTS = {
    "southern_East_Pacific_Rise": "East_Pacific_Rise",
    "Japan_region": "Japan",
    "Volcano_Islands_Japan_region": "Volcano_Islands",
    "Papua_New_Guinea_region": "Papua_New_Guinea",
}

KNOWN_LOW_CONFIDENCE_PAGE_TITLES = {
    "Darien",
    "Lorengau",
    "Tual",
    "Volcano_Islands",
    "Wadomari",
}

KNOWN_REGION_PAGE_TITLES = {
    "Tōhoku_region",
}

DIRECTIONAL_ADJECTIVES = [
    "central",
    "eastern",
    "northern",
    "southern",
    "western",
]

GEOLOGIC_CONTEXT_RULES = [
    (
        "east pacific rise",
        ["East_Pacific_Rise", "Pacific_Ocean", "Mid-ocean_ridge"],
        "regional geological feature in location phrase",
    ),
    (
        "mid-atlantic ridge",
        ["Mid-Atlantic_Ridge", "Atlantic_Ocean", "Mid-ocean_ridge"],
        "regional geological feature in location phrase",
    ),
    (
        "pacific",
        ["Pacific_Ocean"],
        "ocean context in location phrase",
    ),
]

COUNTRY_RULES = {
    "Japan": ["Japan"],
    "Indonesia": ["Indonesia"],
    "Chile": ["Chile"],
    "Peru": ["Peru"],
    "Turkey": ["Turkey"],
    "Tonga": ["Tonga"],
    "Papua New Guinea": ["Papua_New_Guinea"],
    "Papua_New_Guinea": ["Papua_New_Guinea"],
    "Russia": ["Russia"],
    "Mexico": ["Mexico"],
    "Philippines": ["Philippines"],
    "New Zealand": ["New_Zealand"],
    "United States": ["United_States"],
    "China": ["China"],
    "Colombia": ["Colombia"],
}

REGION_RULES = {
    "Ōfunato": ["Ōfunato", "Tōhoku_region"],
    "Ofunato": ["Ōfunato", "Tōhoku_region"],
    "Iwate": ["Iwate_Prefecture", "Tōhoku_region"],
    "Tohoku": ["Tōhoku_region"],
    "Tōhoku": ["Tōhoku_region"],
    "Severo-Kuril": ["Severo-Kurilsk", "Kuril_Islands"],
    "Kuril": ["Kuril_Islands"],
}

SEA_TERMS = [
    "ocean",
    "sea",
    "rise",
    "ridge",
    "trench",
    "island",
    "islands",
    "offshore",
]


def parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError("date must use YYYY-MM-DD format") from exc


def isoformat_utc(value):
    if value is None:
        return "unknown"
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


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


def payload_column(columns):
    for name in ["normalized_payload", "payload", "event_payload", "metadata"]:
        if name in columns:
            return name
    return None


def fetch_events(conn, target_date, limit):
    columns = table_columns(conn, "normalized_events")
    payload_name = payload_column(columns)
    payload_select = payload_name if payload_name else "'{}'::jsonb"
    start = datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc)
    end = start + timedelta(days=1)

    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT
              id,
              title,
              event_time,
              category,
              event_type,
              magnitude_value,
              location_label,
              anomaly_score,
              {payload_select} AS normalized_payload
            FROM normalized_events
            WHERE event_time >= %s
              AND event_time < %s
              AND category = 'geophysical'
              AND event_type = 'earthquake'
            ORDER BY
              anomaly_score DESC NULLS LAST,
              magnitude_value DESC NULLS LAST,
              event_time DESC NULLS LAST
            LIMIT %s
            """,
            (start, end, limit * 5),
        )
        rows = cur.fetchall()

    events = []
    seen_keys = set()
    seen_titles = set()
    for row in rows:
        event_time = row[2]
        event_time_key = event_time.isoformat() if event_time else ""
        event_key = (row[4], event_time_key, row[1])
        title_key = row[1]
        if event_key in seen_keys or title_key in seen_titles:
            continue
        seen_keys.add(event_key)
        seen_titles.add(title_key)
        events.append({
            "id": row[0],
            "title": row[1],
            "event_time": event_time,
            "category": row[3],
            "event_type": row[4],
            "magnitude_value": row[5],
            "location_label": row[6],
            "anomaly_score": row[7],
            "normalized_payload": row[8] or {},
        })
        if len(events) >= limit:
            break

    return events


def strip_distance_prefix(location):
    if not location:
        return ""
    return re.sub(
        r"^\s*\d+(?:\.\d+)?\s*km\s+[A-Z]{1,3}\s+of\s+",
        "",
        location,
        flags=re.IGNORECASE,
    ).strip()


def normalize_page_title(value):
    value = (value or "").strip()
    value = re.sub(r"\s+", " ", value)
    value = value.strip(" ,.;:()[]{}")
    if not value:
        return None
    value = value.replace(" ", "_")
    value = re.sub(r"__+", "_", value)
    return value


def cleanup_candidate_title(title):
    title = normalize_page_title(title)
    if not title:
        return None, False

    if title in KNOWN_PAGE_REPLACEMENTS:
        return KNOWN_PAGE_REPLACEMENTS[title], True

    for adjective in DIRECTIONAL_ADJECTIVES:
        prefix = f"{adjective}_"
        if title.lower().startswith(prefix):
            trimmed = title[len(prefix) :]
            if trimmed in KNOWN_PAGE_REPLACEMENTS:
                return KNOWN_PAGE_REPLACEMENTS[trimmed], True
            if trimmed in {"East_Pacific_Rise", "Mid-Atlantic_Ridge"}:
                return trimmed, True

    if title.endswith("_region") and title not in KNOWN_REGION_PAGE_TITLES:
        base = title[: -len("_region")]
        if base in COUNTRY_RULES or base in KNOWN_PAGE_REPLACEMENTS.values():
            return base, True
        return None, False

    return title, False


def add_unique(items, title, confidence, reason):
    if not title:
        return
    original_title = normalize_page_title(title)
    title, cleaned = cleanup_candidate_title(title)
    if not title:
        return
    if confidence == "low" and reason == "location phrase candidate":
        if title not in KNOWN_LOW_CONFIDENCE_PAGE_TITLES and not cleaned:
            return
    if cleaned:
        confidence = "high"
        reason = f"known cleanup replacement for {original_title}"
    if title.lower() in {item["title"].lower() for item in items}:
        return
    items.append({"title": title, "confidence": confidence, "reason": reason})


def load_registry(path=DEFAULT_REGISTRY_PATH):
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return []
    if not isinstance(data, list):
        return []
    return [entry for entry in data if isinstance(entry, dict)]


def event_match_text(event, location):
    text = " ".join(
        [
            str(event.get("title") or ""),
            str(location or ""),
            str(event.get("event_type") or ""),
            str(event.get("category") or ""),
        ]
    )
    return text.replace("_", " ").lower()


def registry_conditions_match(entry, event, location):
    conditions = entry.get("conditions") or {}
    min_magnitude = conditions.get("min_magnitude")
    if min_magnitude is not None:
        try:
            magnitude = float(event.get("magnitude_value"))
        except (TypeError, ValueError):
            return False
        if magnitude < float(min_magnitude):
            return False
    if conditions.get("sea_like_location") and not is_sea_like(location):
        return False
    return True


def registry_entry_matches(entry, event, location):
    if entry.get("event_type") != event.get("event_type"):
        return False
    if not registry_conditions_match(entry, event, location):
        return False
    pattern = str(entry.get("match_pattern") or "").strip()
    if pattern == "*":
        return True
    if not pattern:
        return False
    match_text = event_match_text(event, location)
    try:
        return re.search(pattern, match_text, flags=re.IGNORECASE) is not None
    except re.error:
        return pattern.lower() in match_text


def registry_candidates(event, location, group):
    pages = []
    for entry in load_registry():
        if entry.get("candidate_group") != group:
            continue
        if not registry_entry_matches(entry, event, location):
            continue
        add_unique(
            pages,
            entry.get("candidate_page"),
            entry.get("confidence") or "low",
            f"registry {entry.get('review_status', 'provisional')}: {entry.get('reason', 'candidate rule')}",
        )
    return pages


def is_sea_like(location):
    text = (location or "").lower()
    return any(term in text for term in SEA_TERMS)


def should_include_tsunami(event, location):
    magnitude = event.get("magnitude_value")
    try:
        magnitude = float(magnitude)
    except (TypeError, ValueError):
        magnitude = None
    return bool(magnitude is not None and magnitude >= 6.0 and is_sea_like(location))


def candidate_core_pages(event, location):
    pages = registry_candidates(event, location, "core")
    for title in CORE_EARTHQUAKE_PAGES:
        add_unique(pages, title, "high", "direct earthquake event type")
    if should_include_tsunami(event, location):
        add_unique(pages, TSUNAMI_PAGE, "medium", "magnitude and location suggest ocean-region context")
    return pages


def candidate_context_pages(event, location):
    pages = registry_candidates(event, location, "context")
    cleaned = strip_distance_prefix(location)
    lower_location = cleaned.lower()

    for needle, titles, reason in GEOLOGIC_CONTEXT_RULES:
        if needle in lower_location:
            for title in titles:
                add_unique(pages, title, "medium", reason)

    for label, titles in COUNTRY_RULES.items():
        if label.lower().replace("_", " ") in lower_location.replace("_", " "):
            for title in titles:
                add_unique(pages, title, "medium", "country or broad region in location phrase")

    for label, titles in REGION_RULES.items():
        if label.lower() in lower_location:
            for title in titles:
                add_unique(pages, title, "low", "specific place or regional context in location phrase")

    for part in cleaned.split(","):
        part = strip_distance_prefix(part)
        title = normalize_page_title(part)
        if title and len(title) >= 3 and not re.match(r"^\d", title):
            add_unique(pages, title, "low", "location phrase candidate")

    return pages


def candidate_historical_pages(_event, _location):
    return registry_candidates(_event, _location, "historical")


def confidence_summary(core_pages, context_pages, historical_pages):
    if core_pages and context_pages:
        return "medium", "core event-type pages and context pages were generated"
    if core_pages:
        return "medium", "core event-type pages were generated"
    if historical_pages:
        return "low", "only historical or broad context pages were generated"
    return "low", "no context page candidates were generated"


def candidate_pages_for_event(event):
    location = event.get("location_label") or ""
    core = candidate_core_pages(event, location)
    context = candidate_context_pages(event, location)
    historical = candidate_historical_pages(event, location)
    confidence, reason = confidence_summary(core, context, historical)
    return {
        "core": core,
        "context": context,
        "historical": historical,
        "confidence": confidence,
        "confidence_reason": reason,
    }


def format_page_list(items):
    if not items:
        return ["- None generated in this dry run."]
    return [
        f"- {item['title']} ({item['confidence']}: {item['reason']})"
        for item in items
    ]


def format_event(event):
    location = event.get("location_label") or "unknown location"
    candidates = candidate_pages_for_event(event)
    magnitude = event.get("magnitude_value")
    magnitude_text = "unknown" if magnitude is None else f"{float(magnitude):.1f}"

    lines = [
        f"## Event: {event['title']}",
        "",
        f"- Event time: {isoformat_utc(event.get('event_time'))}",
        f"- Category: {event.get('category')}",
        f"- Event type: {event.get('event_type')}",
        f"- Magnitude: {magnitude_text}",
        f"- Location phrase: {location}",
        "",
        "### Candidate Core Pages",
        *format_page_list(candidates["core"]),
        "",
        "### Candidate Context Pages",
        *format_page_list(candidates["context"]),
        "",
        "### Candidate Historical/Context Pages",
        *format_page_list(candidates["historical"]),
        "",
        "### Candidate Confidence",
        f"- {candidates['confidence']}: {candidates['confidence_reason']}",
        "",
        "### What We Still Need To Measure",
        "- Pageview activity in +24h / +48h / +7d windows.",
        "- Whether candidate pages exist.",
        "- Whether activity is event-specific or background traffic.",
        "",
        "### What Not To Claim",
        "- Do not claim awareness.",
        "- Do not claim emergency relevance.",
        "- Do not claim prediction.",
        "- Do not claim that absence from candidate pages means absence of public attention.",
        "",
    ]
    return "\n".join(lines)


def build_markdown(events_by_date, limit):
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "# Event-Level Entity Linking Dry Run",
        "",
        f"Generated at: {generated_at}",
        "",
        "## Purpose",
        "",
        "Test whether selected reality events can produce plausible candidate reference pages for later event-specific reflection checks.",
        "",
        "## Method",
        "",
        f"For each selected data date, the script reads up to {limit} geophysical earthquake events from `normalized_events`, then generates registry-prioritized candidate reference pages with heuristic fallback. It does not call external APIs and does not measure page activity.",
        "",
    ]

    for date_text, events in events_by_date.items():
        lines.extend([f"## {date_text}", ""])
        if not events:
            lines.extend(["No earthquake events found for this date.", ""])
            continue
        for event in events:
            lines.append(format_event(event))

    lines.extend(
        [
            "## Initial Assessment",
            "",
            "- Candidate pages can be generated for selected earthquake events.",
            "- Current candidates are heuristic.",
            "- Event-specific reflection cannot yet be measured.",
            "- Next step is page existence and pageview-window measurement.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_dates(args):
    if args.dates:
        return [parse_date(value.strip()) for value in args.dates.split(",") if value.strip()]
    if args.date:
        return [args.date]
    raise argparse.ArgumentTypeError("provide --date or --dates")


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Dry-run candidate reference-page linking for World Pulse reality events."
    )
    parser.add_argument("--date", type=parse_date, default=None, help="Data date in YYYY-MM-DD format.")
    parser.add_argument(
        "--dates",
        default=None,
        help="Comma-separated data dates in YYYY-MM-DD format.",
    )
    parser.add_argument("--limit", type=int, default=3, help="Maximum events per date.")
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL"),
        help="PostgreSQL connection URL. Defaults to DATABASE_URL.",
    )
    parser.add_argument(
        "--output",
        default="examples_entity_linking_dryrun.md",
        help="Markdown output path.",
    )
    args = parser.parse_args()

    if not args.database_url:
        print("DATABASE_URL is required.")
        return 2
    if args.limit <= 0:
        print("--limit must be greater than zero.")
        return 2

    try:
        target_dates = parse_dates(args)
    except argparse.ArgumentTypeError as exc:
        print(str(exc))
        return 2

    events_by_date = {}
    with psycopg.connect(args.database_url) as conn:
        for target_date in target_dates:
            events_by_date[target_date.isoformat()] = fetch_events(conn, target_date, args.limit)

    markdown = build_markdown(events_by_date, args.limit)
    with open(args.output, "w", encoding="utf-8") as file:
        file.write(markdown)

    total_events = sum(len(events) for events in events_by_date.values())
    print(
        "Entity linking dry run completed: "
        f"dates={len(events_by_date)} events={total_events} output={args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
