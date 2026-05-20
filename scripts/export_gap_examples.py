#!/usr/bin/env python3
import argparse
import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import psycopg
from dotenv import load_dotenv


DEFAULT_DAYS = 30
DEFAULT_LIMIT = 10
SCORE_VERSION = "weirdness_v0_2"
NON_TOPIC_PAGE_PREFIXES = (
    "Special:",
    "Wikipedia:",
    "Help:",
    "File:",
    "Category:",
    "Portal:",
    "Template:",
    "Talk:",
    "MediaWiki:",
    "Module:",
    "User:",
    "User_talk:",
    "Draft:",
    "TimedText:",
)
TARGETED_ATTENTION_PAGES = {
    "geophysical": {
        "core": [
            "Earthquake",
            "Tsunami",
            "Seismology",
            "Seismic_wave",
        ],
        "context": [
            "Japan",
            "Turkey",
            "Indonesia",
            "Chile",
            "Peru",
            "Tonga",
            "Papua_New_Guinea",
        ],
    },
    "space_weather": {
        "core": [
            "Solar_flare",
            "Geomagnetic_storm",
            "Aurora",
            "Space_weather",
            "Sunspot",
        ],
        "context": [],
    },
    "internet": {
        "core": [
            "Internet_outage",
            "Cloudflare",
            "Border_Gateway_Protocol",
            "Domain_Name_System",
        ],
        "context": [
            "Internet",
        ],
    },
}


def parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError("date must use YYYY-MM-DD format") from exc


def isoformat_z(value):
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def format_number(value):
    if value is None:
        return "n/a"
    if isinstance(value, int):
        return str(value)
    number = float(value)
    if number.is_integer():
        return str(int(number))
    return f"{number:.2f}"


def format_event_time(value):
    if not value:
        return "time unavailable"
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return str(value)
    parsed = parsed.astimezone(timezone.utc)
    return parsed.strftime("%Y-%m-%d %H:%M UTC")


def int_or_none(value):
    if value is None:
        return None
    return int(value)


def article_views(article):
    if not isinstance(article, dict):
        return 0
    return int(article.get("views") or 0)


def is_topic_page(title):
    if title is None:
        return False
    text = str(title).strip()
    if text == "" or text == "-" or text.lower() == "null":
        return False
    if text == "Main_Page":
        return False
    if "Talk:" in text:
        return False
    return not text.startswith(NON_TOPIC_PAGE_PREFIXES)


def normalize_page_title(title):
    return str(title or "").strip().replace(" ", "_").lower()


def targeted_attention_lookup():
    lookup = {}
    for category, groups in TARGETED_ATTENTION_PAGES.items():
        for target_kind, pages in groups.items():
            for page in pages:
                lookup[normalize_page_title(page)] = {
                    "category": category,
                    "page": page,
                    "target_kind": target_kind,
                }
    return lookup


TARGETED_ATTENTION_LOOKUP = targeted_attention_lookup()


def targeted_attention_matches(top_articles):
    matches = []
    seen = set()
    for article in top_articles:
        title = article.get("article") if isinstance(article, dict) else None
        key = normalize_page_title(title)
        target = TARGETED_ATTENTION_LOOKUP.get(key)
        if not target or key in seen:
            continue
        seen.add(key)
        matches.append(
            {
                "page": target["page"],
                "matched_title": title,
                "category": target["category"],
                "target_kind": target["target_kind"],
                "views": article_views(article),
            }
        )
    return matches


def fetch_scores(conn, start_date, end_date):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT score_date, score_value, component_scores, explanation_payload
            FROM weirdness_scores
            WHERE score_version = %s
              AND score_date >= %s
              AND score_date <= %s
              AND component_scores ? 'layer_gaps'
            ORDER BY score_date DESC
            """,
            (SCORE_VERSION, start_date, end_date),
        )
        rows = cur.fetchall()

    records = []
    for score_date, score_value, component_scores, explanation_payload in rows:
        component_scores = component_scores or {}
        explanation_payload = explanation_payload or {}
        positions = component_scores.get("layer_positions") or {}
        gaps = component_scores.get("layer_gaps") or {}
        raw_scores = component_scores.get("layer_raw_scores") or {}
        sample_counts = component_scores.get("layer_sample_counts") or {}
        raw_scores_excluding_main = (
            component_scores.get("layer_raw_scores_excluding_main_page") or {}
        )
        positions_excluding_main = (
            component_scores.get("layer_positions_excluding_main_page") or {}
        )
        gaps_excluding_main = component_scores.get("layer_gaps_excluding_main_page") or {}
        raw_scores_topic_pages = component_scores.get("layer_raw_scores_topic_pages") or {}
        positions_topic_pages = component_scores.get("layer_positions_topic_pages") or {}
        gaps_topic_pages = component_scores.get("layer_gaps_topic_pages") or {}
        raw_scores_targeted = component_scores.get("layer_raw_scores_targeted") or {}
        positions_targeted = component_scores.get("layer_positions_targeted") or {}
        gaps_targeted = component_scores.get("layer_gaps_targeted") or {}
        raw_scores_targeted_core = (
            component_scores.get("layer_raw_scores_targeted_core") or {}
        )
        positions_targeted_core = (
            component_scores.get("layer_positions_targeted_core") or {}
        )
        gaps_targeted_core = component_scores.get("layer_gaps_targeted_core") or {}
        raw_scores_targeted_context = (
            component_scores.get("layer_raw_scores_targeted_context") or {}
        )
        positions_targeted_context = (
            component_scores.get("layer_positions_targeted_context") or {}
        )
        gaps_targeted_context = component_scores.get("layer_gaps_targeted_context") or {}
        attention_streams = component_scores.get("attention_streams") or {}
        reality_position = int_or_none(positions.get("reality"))
        attention_position = int_or_none(positions.get("attention"))
        difference = (
            reality_position - attention_position
            if reality_position is not None and attention_position is not None
            else None
        )
        records.append(
            {
                "score_date": score_date,
                "score_value": score_value,
                "component_scores": component_scores,
                "explanation_payload": explanation_payload,
                "layer_positions": positions,
                "layer_gaps": gaps,
                "layer_raw_scores": raw_scores,
                "layer_sample_counts": sample_counts,
                "layer_raw_scores_excluding_main_page": raw_scores_excluding_main,
                "layer_positions_excluding_main_page": positions_excluding_main,
                "layer_gaps_excluding_main_page": gaps_excluding_main,
                "layer_raw_scores_topic_pages": raw_scores_topic_pages,
                "layer_positions_topic_pages": positions_topic_pages,
                "layer_gaps_topic_pages": gaps_topic_pages,
                "layer_raw_scores_targeted": raw_scores_targeted,
                "layer_positions_targeted": positions_targeted,
                "layer_gaps_targeted": gaps_targeted,
                "layer_raw_scores_targeted_core": raw_scores_targeted_core,
                "layer_positions_targeted_core": positions_targeted_core,
                "layer_gaps_targeted_core": gaps_targeted_core,
                "layer_raw_scores_targeted_context": raw_scores_targeted_context,
                "layer_positions_targeted_context": positions_targeted_context,
                "layer_gaps_targeted_context": gaps_targeted_context,
                "attention_streams": attention_streams,
                "reality_position": reality_position,
                "attention_position": attention_position,
                "difference": difference,
                "reality_attention_gap": gaps.get("reality_attention_gap"),
                "attention_overhang": gaps.get("attention_overhang"),
            }
        )
    return records


def fetch_layer_observations(conn, start_date, end_date):
    window_start = datetime(start_date.year, start_date.month, start_date.day, tzinfo=timezone.utc)
    window_end = datetime(end_date.year, end_date.month, end_date.day, tzinfo=timezone.utc) + timedelta(days=1)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                ne.event_time::date AS event_date,
                s.layer,
                ne.title,
                ne.event_time,
                ne.category,
                ne.event_type,
                ne.anomaly_score,
                ne.normalized_payload,
                ro.raw_payload
            FROM normalized_events ne
            JOIN sources s ON s.id = ne.source_id
            LEFT JOIN raw_observations ro ON ro.id = ne.raw_observation_id
            WHERE ne.event_time >= %s
              AND ne.event_time < %s
              AND s.layer IN ('reality', 'attention')
            ORDER BY
                event_date ASC,
                s.layer ASC,
                GREATEST(COALESCE(ne.anomaly_score, 0), 0) DESC,
                COALESCE(ne.anomaly_score, 0) DESC,
                ne.event_time DESC
            """,
            (window_start, window_end),
        )
        rows = cur.fetchall()

    observations = {}
    seen_keys = {}
    for row in rows:
        event_date, layer, title, event_time, category, event_type, anomaly_score, payload, raw_payload = row
        by_date = observations.setdefault(event_date, {"reality": [], "attention": []})
        by_date_seen = seen_keys.setdefault(event_date, {"reality": set(), "attention": set()})
        event_key = (
            str(title),
            event_time.isoformat() if hasattr(event_time, "isoformat") else str(event_time),
            str(event_type),
        )
        if event_key in by_date_seen[layer]:
            continue
        if len(by_date[layer]) >= 3:
            continue
        by_date_seen[layer].add(event_key)
        by_date[layer].append(
            {
                "title": title,
                "event_time": event_time,
                "category": category,
                "event_type": event_type,
                "anomaly_score": anomaly_score,
                "normalized_payload": raw_payload if (raw_payload or {}).get("records") else (payload or {}),
            }
        )
    return observations


def observation_line(event):
    title = event.get("title") or "Untitled observation"
    event_time = format_event_time(event.get("event_time"))
    category = event.get("category") or "category unavailable"
    event_type = event.get("event_type") or "type unavailable"
    return f"- {title} — {event_time} — {category} / {event_type}"


def global_topic_attention_details(event):
    payload = event.get("normalized_payload") or {}
    if event.get("event_type") != "wikipedia_attention_snapshot":
        return []

    details = []
    top_articles = payload.get("top_articles") or payload.get("records") or []
    topic_articles = [article for article in top_articles if is_topic_page(article.get("article"))]
    if topic_articles:
        top_page = topic_articles[0].get("article")
        if top_page:
            details.append(f"  - Top topic page: {top_page}")
        details.append(
            f"  - Total topic views: {format_number(sum(article_views(article) for article in topic_articles))}"
        )
    else:
        details.append("  - No topic-level attention observations available for this date.")
    if payload.get("date"):
        details.append(f"  - Date: {payload.get('date')}")
    return details


def targeted_attention_details(record, event):
    streams = record.get("attention_streams") or {}
    targeted_core = streams.get("targeted_core") or {}
    targeted_context = streams.get("targeted_context") or {}
    core_matches = targeted_core.get("matched_pages")
    context_matches = targeted_context.get("matched_pages")
    if core_matches is None or context_matches is None:
        payload = event.get("normalized_payload") or {}
        matches = targeted_attention_matches(payload.get("top_articles") or payload.get("records") or [])
        if core_matches is None:
            core_matches = [
                match for match in matches if match.get("target_kind") == "core"
            ]
        if context_matches is None:
            context_matches = [
                match for match in matches if match.get("target_kind") == "context"
            ]

    details = ["Targeted attention:"]
    if core_matches:
        details.append("Core matched pages:")
        for match in core_matches:
            details.append(
                f"- {match.get('page')} — views: {format_number(match.get('views'))}"
            )
    else:
        details.append("Core matched pages:")
        details.append("- No core targeted attention pages found in stored Wikipedia top pages for this date.")
    if context_matches:
        details.append("")
        details.append("Context matched pages:")
        for match in context_matches:
            details.append(
                f"- {match.get('page')} — views: {format_number(match.get('views'))}"
            )
    else:
        details.append("")
        details.append("Context matched pages:")
        details.append("- No context targeted attention pages found in stored Wikipedia top pages for this date.")
    details.append(
        ""
    )
    details.append(
        "- Total core targeted views: "
        f"{format_number((record.get('layer_raw_scores_targeted_core') or {}).get('attention'))}"
    )
    details.append(
        "- Core Targeted Attention Position: "
        f"{format_number((record.get('layer_positions_targeted_core') or {}).get('attention'))}"
    )
    details.append(
        "- Reality-Core Targeted Attention difference: "
        f"{format_number((record.get('layer_gaps_targeted_core') or {}).get('reality_attention_gap'))}"
    )
    details.append(
        "- Total context targeted views: "
        f"{format_number((record.get('layer_raw_scores_targeted_context') or {}).get('attention'))}"
    )
    details.append(
        "- Context Targeted Attention Position: "
        f"{format_number((record.get('layer_positions_targeted_context') or {}).get('attention'))}"
    )
    details.append(
        "- Reality-Context Targeted Attention difference: "
        f"{format_number((record.get('layer_gaps_targeted_context') or {}).get('reality_attention_gap'))}"
    )
    return details


def append_layer_observations(lines, title, observations, layer, record=None):
    lines.append(title)
    events = observations.get(layer, [])
    if not events:
        lines.append("- No observations available for this layer in stored events.")
        if layer == "attention" and record is not None:
            lines.extend(targeted_attention_details(record, {}))
        lines.append("")
        return
    for event in events:
        if layer == "attention":
            lines.append("Global topic attention:")
            lines.extend(global_topic_attention_details(event))
            lines.extend(targeted_attention_details(record or {}, event))
        else:
            lines.append(observation_line(event))
    lines.append("")


def append_record(lines, record):
    raw_scores = record["layer_raw_scores"]
    raw_scores_excluding_main = record["layer_raw_scores_excluding_main_page"]
    positions_excluding_main = record["layer_positions_excluding_main_page"]
    gaps_excluding_main = record["layer_gaps_excluding_main_page"]
    raw_scores_topic_pages = record["layer_raw_scores_topic_pages"]
    positions_topic_pages = record["layer_positions_topic_pages"]
    gaps_topic_pages = record["layer_gaps_topic_pages"]
    raw_scores_targeted_core = record["layer_raw_scores_targeted_core"]
    positions_targeted_core = record["layer_positions_targeted_core"]
    gaps_targeted_core = record["layer_gaps_targeted_core"]
    raw_scores_targeted_context = record["layer_raw_scores_targeted_context"]
    positions_targeted_context = record["layer_positions_targeted_context"]
    gaps_targeted_context = record["layer_gaps_targeted_context"]
    sample_counts = record["layer_sample_counts"]
    lines.extend(
        [
            f"### {record['score_date'].isoformat()}",
            "",
            f"- Signal Position: {format_number(record['score_value'])}",
            f"- Reality Position: {format_number(record['reality_position'])}",
            f"- Attention Position: {format_number(record['attention_position'])}",
            f"- Reality-Attention difference: {format_number(record['difference'])}",
            f"- Reality raw score: {format_number(raw_scores.get('reality'))}",
            f"- Attention raw score: {format_number(raw_scores.get('attention'))}",
            (
                "- Attention raw score excluding Main Page: "
                f"{format_number(raw_scores_excluding_main.get('attention'))}"
            ),
            (
                "- Attention Position excluding Main Page: "
                f"{format_number(positions_excluding_main.get('attention'))}"
            ),
            (
                "- Reality-Attention difference excluding Main Page: "
                f"{format_number(gaps_excluding_main.get('reality_attention_gap'))}"
            ),
            (
                "- Attention raw score topic pages: "
                f"{format_number(raw_scores_topic_pages.get('attention'))}"
            ),
            (
                "- Attention Position topic pages: "
                f"{format_number(positions_topic_pages.get('attention'))}"
            ),
            (
                "- Reality-Attention difference topic pages: "
                f"{format_number(gaps_topic_pages.get('reality_attention_gap'))}"
            ),
            (
                "- Attention raw score targeted core: "
                f"{format_number(raw_scores_targeted_core.get('attention'))}"
            ),
            (
                "- Attention Position targeted core: "
                f"{format_number(positions_targeted_core.get('attention'))}"
            ),
            (
                "- Reality-Attention difference targeted core: "
                f"{format_number(gaps_targeted_core.get('reality_attention_gap'))}"
            ),
            (
                "- Attention raw score targeted context: "
                f"{format_number(raw_scores_targeted_context.get('attention'))}"
            ),
            (
                "- Attention Position targeted context: "
                f"{format_number(positions_targeted_context.get('attention'))}"
            ),
            (
                "- Reality-Attention difference targeted context: "
                f"{format_number(gaps_targeted_context.get('reality_attention_gap'))}"
            ),
            (
                "- Layer sample counts: "
                f"reality={format_number(sample_counts.get('reality'))}, "
                f"attention={format_number(sample_counts.get('attention'))}"
            ),
            "",
        ]
    )
    observations = record.get("layer_observations") or {}
    append_layer_observations(lines, "Top reality observations:", observations, "reality")
    append_layer_observations(lines, "Top attention observations:", observations, "attention", record=record)


def section_higher_reality(records, limit):
    filtered = [
        record
        for record in records
        if record["reality_attention_gap"] is not None
        and record["reality_attention_gap"] > 0
        and record["reality_position"] is not None
        and record["attention_position"] is not None
        and record["reality_position"] >= 70
        and record["attention_position"] <= 50
    ]
    return sorted(
        filtered,
        key=lambda record: (record["reality_attention_gap"], record["score_date"]),
        reverse=True,
    )[:limit]


def section_higher_attention(records, limit):
    filtered = [
        record
        for record in records
        if record["attention_overhang"] is not None
        and record["attention_overhang"] > 0
        and record["reality_position"] is not None
        and record["attention_position"] is not None
        and record["attention_position"] >= 70
        and record["reality_position"] <= 50
    ]
    return sorted(
        filtered,
        key=lambda record: (record["attention_overhang"], record["score_date"]),
        reverse=True,
    )[:limit]


def section_largest_differences(records, limit):
    filtered = [record for record in records if record["difference"] is not None]
    return sorted(
        filtered,
        key=lambda record: (abs(record["difference"]), record["score_date"]),
        reverse=True,
    )[:limit]


def append_section(lines, title, records):
    lines.extend([f"## {title}", ""])
    if not records:
        lines.extend(["No matching dates found for this window.", ""])
        return
    for record in records:
        append_record(lines, record)


def build_markdown(records, generated_at, start_date, end_date, limit):
    lines = [
        "# World Pulse Gap Examples",
        "",
        f"Generated at: {isoformat_z(generated_at)}",
        "",
        "## Scope",
        "",
        "This file is for internal validation.",
        "Layer gaps are not forecasts, alerts, warnings, or recommendations.",
        (
            "They are internal research fields comparing relative positions between "
            "source layers."
        ),
        "",
        f"Date range: {start_date.isoformat()} to {end_date.isoformat()}",
        f"Rows evaluated: {len(records)}",
        "",
    ]
    append_section(
        lines,
        "1. Higher reality position than attention position",
        section_higher_reality(records, limit),
    )
    append_section(
        lines,
        "2. Higher attention position than reality position",
        section_higher_attention(records, limit),
    )
    append_section(
        lines,
        "3. Largest absolute layer differences",
        section_largest_differences(records, limit),
    )
    lines.extend(
        [
            "## 4. Notes for interpretation",
            "",
            "- Layer differences are internal validation fields.",
            "- A higher reality position does not mean danger.",
            "- A higher attention position does not mean overreaction.",
            (
                "- These values only compare relative positions of currently tracked "
                "public source layers."
            ),
            (
                "- Current attention layer is limited mainly to Wikipedia Pageviews, "
                "so conclusions must be treated as provisional."
            ),
            (
                "- Current attention layer is limited. In this beta, Wikipedia "
                "Pageviews is only a rough public attention proxy and does not "
                "represent total public awareness."
            ),
            (
                "- Global topic attention reflects broad Wikipedia topic traffic and "
                "may not correspond to the selected reality observations."
            ),
            (
                "- Targeted attention only checks whether predefined topic pages "
                "appear in stored Wikipedia top pages."
            ),
            (
                "- Core targeted pages are topic pages directly related to the "
                "observed category."
            ),
            (
                "- Context targeted pages are broader location or infrastructure "
                "context pages."
            ),
            (
                "- Context matches must not be interpreted as direct attention to "
                "a specific event."
            ),
            (
                "- Absence from targeted attention does not imply absence of public "
                "awareness."
            ),
            "- Main_Page is excluded from topic-level attention inspection where available.",
            (
                "- Topic-level attention excludes Main_Page and non-topic Wikipedia "
                "namespace pages such as Special:, Wikipedia:, Help:, File:, and Category:."
            ),
            "- Wikipedia Pageviews remains a rough public attention proxy.",
            "",
        ]
    )
    return "\n".join(lines)


def resolve_date_range(args):
    today = datetime.now(timezone.utc).date()
    end_date = args.end_date or today
    if args.start_date:
        start_date = args.start_date
    else:
        start_date = end_date - timedelta(days=args.days - 1)
    if start_date > end_date:
        raise ValueError("--start-date must be before or equal to --end-date")
    return start_date, end_date


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Export internal World Pulse layer gap examples.")
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS, help="Lookback days.")
    parser.add_argument("--start-date", type=parse_date, default=None, help="Start date YYYY-MM-DD.")
    parser.add_argument("--end-date", type=parse_date, default=None, help="End date YYYY-MM-DD.")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="Examples per section.")
    parser.add_argument("--output", default="examples.md", help="Markdown output path.")
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL"),
        help="PostgreSQL connection URL. Defaults to DATABASE_URL.",
    )
    args = parser.parse_args()

    if args.days <= 0:
        print("--days must be greater than zero.", file=sys.stderr)
        return 2
    if args.limit <= 0:
        print("--limit must be greater than zero.", file=sys.stderr)
        return 2
    if not args.database_url:
        print("DATABASE_URL is required.", file=sys.stderr)
        return 2

    try:
        start_date, end_date = resolve_date_range(args)
        with psycopg.connect(args.database_url) as conn:
            records = fetch_scores(conn, start_date, end_date)
            layer_observations = fetch_layer_observations(conn, start_date, end_date)
        for record in records:
            record["layer_observations"] = layer_observations.get(
                record["score_date"],
                {"reality": [], "attention": []},
            )
        markdown = build_markdown(records, datetime.now(timezone.utc), start_date, end_date, args.limit)
        output_path = Path(args.output)
        output_path.write_text(markdown, encoding="utf-8")
    except Exception as exc:
        print(f"Gap examples export failed: {exc}", file=sys.stderr)
        return 1

    print(
        "Gap examples export completed: "
        f"rows={len(records)} "
        f"start_date={start_date.isoformat()} "
        f"end_date={end_date.isoformat()} "
        f"output={output_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
