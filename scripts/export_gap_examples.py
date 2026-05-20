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
                ne.normalized_payload
            FROM normalized_events ne
            JOIN sources s ON s.id = ne.source_id
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
        event_date, layer, title, event_time, category, event_type, anomaly_score, payload = row
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
                "normalized_payload": payload or {},
            }
        )
    return observations


def observation_line(event):
    title = event.get("title") or "Untitled observation"
    event_time = format_event_time(event.get("event_time"))
    category = event.get("category") or "category unavailable"
    event_type = event.get("event_type") or "type unavailable"
    return f"- {title} — {event_time} — {category} / {event_type}"


def attention_details(event):
    payload = event.get("normalized_payload") or {}
    if event.get("event_type") != "wikipedia_attention_snapshot":
        return []

    details = []
    top_articles = payload.get("top_articles") or []
    topic_articles = [
        article
        for article in top_articles
        if article.get("article") != "Main_Page"
    ]
    if topic_articles:
        top_page = topic_articles[0].get("article")
        if top_page:
            details.append(f"  - Top page: {top_page}")
    if payload.get("top10_total_views_excluding_main_page") is not None:
        details.append(
            "  - Total views excluding Main Page: "
            f"{format_number(payload.get('top10_total_views_excluding_main_page'))}"
        )
    if payload.get("date"):
        details.append(f"  - Date: {payload.get('date')}")
    if not details:
        details.append("  - Details unavailable in current normalized event payload.")
    return details


def append_layer_observations(lines, title, observations, layer):
    lines.append(title)
    events = observations.get(layer, [])
    if not events:
        lines.append("- No observations available for this layer in stored events.")
        lines.append("")
        return
    for event in events:
        lines.append(observation_line(event))
        if layer == "attention":
            lines.extend(attention_details(event))
    lines.append("")


def append_record(lines, record):
    raw_scores = record["layer_raw_scores"]
    raw_scores_excluding_main = record["layer_raw_scores_excluding_main_page"]
    positions_excluding_main = record["layer_positions_excluding_main_page"]
    gaps_excluding_main = record["layer_gaps_excluding_main_page"]
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
                "- Layer sample counts: "
                f"reality={format_number(sample_counts.get('reality'))}, "
                f"attention={format_number(sample_counts.get('attention'))}"
            ),
            "",
        ]
    )
    observations = record.get("layer_observations") or {}
    append_layer_observations(lines, "Top reality observations:", observations, "reality")
    append_layer_observations(lines, "Top attention observations:", observations, "attention")


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
            "- Main_Page is excluded from topic-level attention inspection where available.",
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
