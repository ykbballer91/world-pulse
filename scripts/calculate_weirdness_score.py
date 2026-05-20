#!/usr/bin/env python3
import argparse
import os
import sys
from datetime import datetime, timedelta, timezone

import psycopg
from dotenv import load_dotenv
from psycopg.types.json import Jsonb


VERSION_KEY = "weirdness_v0_2"
FORMULA_TEXT = (
    "Daily raw score is computed from the top positive anomaly scores for each observed day. "
    "The displayed Signal Position is the percentile rank of the selected data date's raw score "
    "within the recent baseline window."
)
TOP_WEIGHTS = [20, 10, 5]
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
DEFAULT_WINDOW_DAYS = 30
VERSION_PARAMETERS = {
    "window_days": DEFAULT_WINDOW_DAYS,
    "top_weights": TOP_WEIGHTS,
    "percentile_method": "midrank",
    "negative_anomaly_policy": "effective_anomaly = max(anomaly_score, 0)",
    "score_range": [0, 100],
}
INTERNAL_LAYER_VERSION_KEY = "weirdness_v0_3_internal_layers"
INTERNAL_LAYER_FORMULA_TEXT = (
    "Same public Signal Position calculation as weirdness_v0_2. Adds internal reality "
    "and attention layer positions and internal reality_attention_gap fields. Not exposed "
    "in public UI."
)
INTERNAL_LAYER_PARAMETERS = {
    "calculation_compatible_with": "weirdness_v0_2",
    "public_label": "Signal Position",
    "internal_layers": ["reality", "attention", "context"],
    "gap_public_exposure": "internal_only",
    "minimum_layer_sample_count": 14,
}
REFLECTION_CONCEPT_VERSION_KEY = "weirdness_v0_4_reflection_concept"
REFLECTION_CONCEPT_FORMULA_TEXT = (
    "Conceptual clarification: Wikipedia pageviews are treated as a delayed "
    "reflection / knowledge-encoding proxy rather than immediate public attention. "
    "DB schema and scoring algorithm are unchanged for backward compatibility. "
    "Public display remains Signal Position."
)
REFLECTION_CONCEPT_PARAMETERS = {
    "calculation_compatible_with": "weirdness_v0_3_internal_layers",
    "public_label": "Signal Position",
    "conceptual_layers": {
        "reality": [
            "USGS Earthquake Hazards Program",
            "NOAA SWPC",
            "Cloudflare Radar",
        ],
        "reflection": [
            "Wikipedia Pageviews",
        ],
        "context": [
            "Open Notify",
        ],
        "immediate_attention": "not_implemented",
        "interpretation": "not_implemented",
        "action": "not_implemented",
    },
    "backward_compatibility": {
        "database_layer_label_retained": "attention",
        "component_score_attention_keys_retained": True,
        "db_schema_changed": False,
    },
    "public_exposure": {
        "public_ui_changed": False,
        "x_post_changed": False,
        "share_image_changed": False,
    },
    "commercial_distribution": {
        "sales_motion": "pull_only",
        "brief": "planned",
        "contact_form": "planned",
        "push_sales_materials": False,
    },
}
MINIMUM_LAYER_SAMPLE_COUNT = 14
LAYER_METHODOLOGY = {
    "public_exposure": "internal_only",
    "gap_interpretation_policy": (
        "Layer positions are internal research fields and are not exposed in public displays."
    ),
    "layers": {
        "reality": [
            "USGS Earthquake Hazards Program",
            "NOAA SWPC",
            "Cloudflare Radar",
        ],
        "attention": ["Wikipedia Pageviews"],
        "context": ["Open Notify"],
    },
}
EXCLUDED_TOP_SIGNAL_EVENT_TYPES = {
    "wikipedia_attention_snapshot",
}

JSON_COLUMNS = [
    "explanation_payload",
    "payload",
    "metadata",
]


def parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--date must use YYYY-MM-DD format") from exc


def isoformat_z(value):
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def article_views(article):
    if not isinstance(article, dict):
        return 0
    value = article.get("views", 0)
    return int(value or 0)


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


def topic_page_total_views(normalized_payload):
    top_articles = normalized_payload.get("top_articles") or normalized_payload.get("records") or []
    return sum(
        article_views(article)
        for article in top_articles
        if is_topic_page(article.get("article"))
    )


def targeted_attention_matches(normalized_payload):
    top_articles = normalized_payload.get("top_articles") or normalized_payload.get("records") or []
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


def latest_observation_date(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT event_time::date
            FROM normalized_events
            WHERE event_time IS NOT NULL
              AND anomaly_score IS NOT NULL
            ORDER BY event_time DESC
            LIMIT 1
            """
        )
        row = cur.fetchone()
        if row is None:
            raise ValueError("no normalized_events with event_time were found")
        return row[0]


def upsert_score_version(conn, columns, version_key, formula_text, parameters):
    required = {"version_key"}
    if not required.issubset(columns):
        raise ValueError("score_versions must include version_key")

    values = {"version_key": version_key}
    if "formula_text" in columns:
        values["formula_text"] = formula_text
    elif "formula" in columns:
        values["formula"] = formula_text
    if "parameters" in columns:
        values["parameters"] = Jsonb(parameters)
    if "updated_at" in columns:
        values["updated_at"] = datetime.now(timezone.utc)

    with conn.cursor() as cur:
        insert_values = dict(values)
        if "created_at" in columns:
            insert_values["created_at"] = datetime.now(timezone.utc)

        insert_columns = list(insert_values)
        placeholders = ", ".join(["%s"] * len(insert_columns))
        column_sql = ", ".join(insert_columns)
        update_columns = [column for column in values if column != "version_key"]
        update_sql = ", ".join(f"{column} = EXCLUDED.{column}" for column in update_columns)
        conflict_sql = f"DO UPDATE SET {update_sql}" if update_sql else "DO NOTHING"
        cur.execute(
            f"""
            INSERT INTO score_versions ({column_sql})
            VALUES ({placeholders})
            ON CONFLICT (version_key) {conflict_sql}
            """,
            [insert_values[column] for column in insert_columns],
        )


def ensure_score_version(conn, columns, window_days):
    parameters = dict(VERSION_PARAMETERS)
    parameters["window_days"] = window_days
    upsert_score_version(conn, columns, VERSION_KEY, FORMULA_TEXT, parameters)

    internal_parameters = dict(INTERNAL_LAYER_PARAMETERS)
    internal_parameters["window_days"] = window_days
    upsert_score_version(
        conn,
        columns,
        INTERNAL_LAYER_VERSION_KEY,
        INTERNAL_LAYER_FORMULA_TEXT,
        internal_parameters,
    )

    reflection_parameters = dict(REFLECTION_CONCEPT_PARAMETERS)
    reflection_parameters["window_days"] = window_days
    upsert_score_version(
        conn,
        columns,
        REFLECTION_CONCEPT_VERSION_KEY,
        REFLECTION_CONCEPT_FORMULA_TEXT,
        reflection_parameters,
    )


def fetch_events_for_window(conn, window_start_date, window_end_date):
    window_start = datetime(
        window_start_date.year,
        window_start_date.month,
        window_start_date.day,
        tzinfo=timezone.utc,
    )
    window_end = datetime(
        window_end_date.year,
        window_end_date.month,
        window_end_date.day,
        tzinfo=timezone.utc,
    ) + timedelta(days=1)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT bd.sample_count, bd.mean_value, bd.stddev_value
            FROM baseline_distributions bd
            JOIN sources s ON s.id = bd.source_id
            WHERE s.name = 'Wikipedia Pageviews'
              AND bd.metric_key = 'wikipedia_daily_top10_total_views_excluding_main_page'
            ORDER BY bd.window_end DESC
            LIMIT 1
            """
        )
        wikipedia_excluding_main_baseline = cur.fetchone()
        cur.execute(
            """
            SELECT
                ne.id,
                ne.event_type,
                ne.category,
                ne.title,
                ne.event_time,
                ne.magnitude_value,
                ne.anomaly_score,
                s.layer,
                ne.normalized_payload,
                ro.raw_payload
            FROM normalized_events ne
            LEFT JOIN sources s ON s.id = ne.source_id
            LEFT JOIN raw_observations ro ON ro.id = ne.raw_observation_id
            WHERE ne.event_time >= %s
              AND ne.event_time < %s
              AND ne.anomaly_score IS NOT NULL
            ORDER BY ne.event_time ASC
            """,
            (window_start, window_end),
        )
        rows = cur.fetchall()

    events = []
    for row in rows:
        normalized_payload = row[8] or {}
        raw_payload = row[9] or {}
        attention_payload = raw_payload if raw_payload.get("records") else normalized_payload
        excluding_main_value = normalized_payload.get("top10_total_views_excluding_main_page")
        excluding_main_anomaly = anomaly_from_baseline(
            excluding_main_value,
            wikipedia_excluding_main_baseline,
        )
        topic_total_views = topic_page_total_views(attention_payload)
        targeted_matches = targeted_attention_matches(attention_payload)
        targeted_total_views = sum(match["views"] for match in targeted_matches)
        events.append(
            {
                "id": row[0],
                "event_type": row[1],
                "category": row[2],
                "title": row[3],
                "event_time": row[4],
                "magnitude_value": row[5],
                "anomaly_score": row[6],
                "effective_anomaly": max(float(row[6]), 0),
                "layer": row[7],
                "normalized_payload": normalized_payload,
                "attention_payload": attention_payload,
                "attention_excluding_main_page_anomaly_score": excluding_main_anomaly,
                "attention_excluding_main_page_effective_anomaly": (
                    max(float(excluding_main_anomaly), 0)
                    if excluding_main_anomaly is not None
                    else None
                ),
                "attention_topic_page_total_views": topic_total_views,
                "attention_topic_page_anomaly_score": None,
                "attention_topic_page_effective_anomaly": None,
                "attention_targeted_total_views": targeted_total_views,
                "attention_targeted_matched_pages": targeted_matches,
            }
        )
    return events


def anomaly_from_baseline(value, baseline):
    if value is None or baseline is None:
        return None
    sample_count, mean_value, stddev_value = baseline
    if sample_count is None or sample_count < 3:
        return None
    if stddev_value in (None, 0):
        return None
    return (float(value) - float(mean_value)) / float(stddev_value)


def sort_events_for_score(events):
    return sorted(
        events,
        key=lambda event: (
            event["effective_anomaly"],
            float(event["anomaly_score"]),
            event["event_time"],
        ),
        reverse=True,
    )


def calculate_daily_raw_score(events):
    scored_events = sort_events_for_score(events)
    top_events = scored_events[:3]
    raw_score = sum(
        weight * event["effective_anomaly"] for weight, event in zip(TOP_WEIGHTS, top_events)
    )
    return raw_score, top_events, scored_events


def calculate_daily_attention_excluding_main_raw_score(events):
    scored_events = sorted(
        [
            event
            for event in events
            if event.get("attention_excluding_main_page_effective_anomaly") is not None
        ],
        key=lambda event: (
            event["attention_excluding_main_page_effective_anomaly"],
            float(event["attention_excluding_main_page_anomaly_score"]),
            event["event_time"],
        ),
        reverse=True,
    )
    top_events = scored_events[:3]
    raw_score = sum(
        weight * event["attention_excluding_main_page_effective_anomaly"]
        for weight, event in zip(TOP_WEIGHTS, top_events)
    )
    return raw_score, top_events, scored_events


def calculate_daily_attention_topic_pages_raw_score(events):
    scored_events = sorted(
        [
            event
            for event in events
            if event.get("attention_topic_page_effective_anomaly") is not None
        ],
        key=lambda event: (
            event["attention_topic_page_effective_anomaly"],
            float(event["attention_topic_page_anomaly_score"]),
            event["event_time"],
        ),
        reverse=True,
    )
    top_events = scored_events[:3]
    raw_score = sum(
        weight * event["attention_topic_page_effective_anomaly"]
        for weight, event in zip(TOP_WEIGHTS, top_events)
    )
    return raw_score, top_events, scored_events


def percentile_rank(values, target_value):
    if not values:
        return None, 0, 0, 0
    less_count = sum(1 for value in values if value < target_value)
    equal_count = sum(1 for value in values if value == target_value)
    percentile = 100 * (less_count + 0.5 * equal_count) / len(values)
    return percentile, less_count, equal_count, len(values)


def rounded_position(percentile):
    if percentile is None:
        return None
    return round(max(0, min(percentile, 100)))


def population_stddev(values):
    if not values:
        return None
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return variance ** 0.5


def assign_topic_page_anomalies(events):
    topic_values = [
        float(event["attention_topic_page_total_views"])
        for event in events
        if event.get("layer") == "attention"
        and event.get("attention_topic_page_total_views") is not None
    ]
    if len(topic_values) < 3:
        return
    mean = sum(topic_values) / len(topic_values)
    stddev = population_stddev(topic_values)
    if stddev in (None, 0):
        return
    for event in events:
        if event.get("layer") != "attention":
            continue
        value = event.get("attention_topic_page_total_views")
        if value is None:
            continue
        anomaly = (float(value) - mean) / stddev
        event["attention_topic_page_anomaly_score"] = anomaly
        event["attention_topic_page_effective_anomaly"] = max(anomaly, 0)


def display_top_events(events):
    display_events = []
    seen_keys = set()
    for event in sort_events_for_score(events):
        if event["event_type"] in EXCLUDED_TOP_SIGNAL_EVENT_TYPES:
            continue
        for key in [
            ("id", str(event["id"])),
            (
                "type_time_title",
                event["event_type"],
                isoformat_z(event["event_time"]),
                event["title"],
            ),
            ("title", event["title"]),
        ]:
            if key in seen_keys:
                break
        else:
            display_events.append(event)
            seen_keys.update(
                [
                    ("id", str(event["id"])),
                    (
                        "type_time_title",
                        event["event_type"],
                        isoformat_z(event["event_time"]),
                        event["title"],
                    ),
                    ("title", event["title"]),
                ]
            )
        if len(display_events) >= 3:
            break
    return display_events


def calculate_window_scores(events, target_date, window_days):
    window_start_date = target_date - timedelta(days=window_days - 1)
    assign_topic_page_anomalies(events)
    events_by_date = {}
    for event in events:
        events_by_date.setdefault(event["event_time"].date(), []).append(event)

    daily_raw_scores = []
    layer_daily_raw_scores = {
        "reality": [],
        "attention": [],
    }
    layer_daily_raw_scores_excluding_main_page = {
        "attention": [],
    }
    layer_daily_raw_scores_topic_pages = {
        "attention": [],
    }
    layer_daily_raw_scores_targeted = {
        "attention": [],
    }
    layer_daily_raw_scores_targeted_core = {
        "attention": [],
    }
    layer_daily_raw_scores_targeted_context = {
        "attention": [],
    }
    target_scoring_top_events = []
    target_display_top_events = []
    target_scored_events = []
    target_layer_raw_scores = {
        "reality": 0,
        "attention": 0,
    }
    target_layer_raw_scores_excluding_main_page = {
        "attention": 0,
    }
    target_layer_raw_scores_topic_pages = {
        "attention": 0,
    }
    target_layer_raw_scores_targeted = {
        "attention": 0,
    }
    target_layer_raw_scores_targeted_core = {
        "attention": 0,
    }
    target_layer_raw_scores_targeted_context = {
        "attention": 0,
    }
    target_targeted_matches = []
    target_targeted_core_matches = []
    target_targeted_context_matches = []
    context_event_count = 0
    for offset in range(window_days):
        day = window_start_date + timedelta(days=offset)
        day_events = events_by_date.get(day, [])
        raw_score, top_events, scored_events = calculate_daily_raw_score(day_events)
        if day == target_date:
            target_scoring_top_events = top_events
            target_display_top_events = display_top_events(day_events)
            target_scored_events = scored_events
            context_event_count = sum(1 for event in day_events if event.get("layer") == "context")
        daily_raw_scores.append(
            {
                "date": day.isoformat(),
                "raw_score": raw_score,
                "event_count": len(day_events),
            }
        )
        for layer in ["reality", "attention"]:
            layer_events = [event for event in day_events if event.get("layer") == layer]
            layer_raw_score, _, _ = calculate_daily_raw_score(layer_events)
            if day == target_date:
                target_layer_raw_scores[layer] = layer_raw_score
            layer_daily_raw_scores[layer].append(
                {
                    "date": day.isoformat(),
                    "raw_score": layer_raw_score,
                    "event_count": len(layer_events),
                    "has_layer_events": bool(layer_events),
                }
            )
        attention_events = [event for event in day_events if event.get("layer") == "attention"]
        attention_excluding_main_raw_score, _, _ = calculate_daily_attention_excluding_main_raw_score(
            attention_events
        )
        if day == target_date:
            target_layer_raw_scores_excluding_main_page["attention"] = (
                attention_excluding_main_raw_score
            )
        layer_daily_raw_scores_excluding_main_page["attention"].append(
            {
                "date": day.isoformat(),
                "raw_score": attention_excluding_main_raw_score,
                "event_count": len(attention_events),
                "has_layer_events": any(
                    event.get("attention_excluding_main_page_anomaly_score") is not None
                    for event in attention_events
                ),
            }
        )
        attention_topic_pages_raw_score, _, _ = calculate_daily_attention_topic_pages_raw_score(
            attention_events
        )
        if day == target_date:
            target_layer_raw_scores_topic_pages["attention"] = attention_topic_pages_raw_score
        layer_daily_raw_scores_topic_pages["attention"].append(
            {
                "date": day.isoformat(),
                "raw_score": attention_topic_pages_raw_score,
                "event_count": len(attention_events),
                "has_layer_events": any(
                    event.get("attention_topic_page_anomaly_score") is not None
                    for event in attention_events
                ),
            }
        )
        attention_targeted_raw_score = sum(
            float(event.get("attention_targeted_total_views") or 0)
            for event in attention_events
        )
        attention_targeted_matches = []
        seen_targeted_pages = set()
        for event in attention_events:
            for match in event.get("attention_targeted_matched_pages") or []:
                key = normalize_page_title(match.get("page"))
                if key in seen_targeted_pages:
                    continue
                seen_targeted_pages.add(key)
                attention_targeted_matches.append(match)
        attention_targeted_matches = sorted(
            attention_targeted_matches,
            key=lambda match: match.get("views") or 0,
            reverse=True,
        )
        attention_targeted_core_matches = [
            match for match in attention_targeted_matches if match.get("target_kind") == "core"
        ]
        attention_targeted_context_matches = [
            match for match in attention_targeted_matches if match.get("target_kind") == "context"
        ]
        attention_targeted_core_raw_score = sum(
            float(match.get("views") or 0) for match in attention_targeted_core_matches
        )
        attention_targeted_context_raw_score = sum(
            float(match.get("views") or 0) for match in attention_targeted_context_matches
        )
        if day == target_date:
            target_layer_raw_scores_targeted["attention"] = attention_targeted_raw_score
            target_layer_raw_scores_targeted_core["attention"] = (
                attention_targeted_core_raw_score
            )
            target_layer_raw_scores_targeted_context["attention"] = (
                attention_targeted_context_raw_score
            )
            target_targeted_matches = attention_targeted_matches
            target_targeted_core_matches = attention_targeted_core_matches
            target_targeted_context_matches = attention_targeted_context_matches
        layer_daily_raw_scores_targeted["attention"].append(
            {
                "date": day.isoformat(),
                "raw_score": attention_targeted_raw_score,
                "event_count": len(attention_events),
                "matched_page_count": len(attention_targeted_matches),
                "has_layer_events": bool(attention_events),
            }
        )
        layer_daily_raw_scores_targeted_core["attention"].append(
            {
                "date": day.isoformat(),
                "raw_score": attention_targeted_core_raw_score,
                "event_count": len(attention_events),
                "matched_page_count": len(attention_targeted_core_matches),
                "has_layer_events": bool(attention_events),
            }
        )
        layer_daily_raw_scores_targeted_context["attention"].append(
            {
                "date": day.isoformat(),
                "raw_score": attention_targeted_context_raw_score,
                "event_count": len(attention_events),
                "matched_page_count": len(attention_targeted_context_matches),
                "has_layer_events": bool(attention_events),
            }
        )

    target_raw_score = next(
        item["raw_score"] for item in daily_raw_scores if item["date"] == target_date.isoformat()
    )
    raw_values = [item["raw_score"] for item in daily_raw_scores]
    percentile_value, less_count, equal_count, sample_count = percentile_rank(raw_values, target_raw_score)
    score_value = rounded_position(percentile_value)

    layer_positions = {}
    layer_sample_counts = {}
    layer_percentile_ranks = {}
    for layer, daily_scores in layer_daily_raw_scores.items():
        layer_values = [
            item["raw_score"] for item in daily_scores if item["has_layer_events"]
        ]
        target_layer_value = target_layer_raw_scores[layer]
        layer_sample_count = len(layer_values)
        layer_sample_counts[layer] = layer_sample_count
        if layer_sample_count >= MINIMUM_LAYER_SAMPLE_COUNT:
            layer_percentile, _, _, _ = percentile_rank(layer_values, target_layer_value)
            layer_percentile_ranks[layer] = layer_percentile
            layer_positions[layer] = rounded_position(layer_percentile)
        else:
            layer_percentile_ranks[layer] = None
            layer_positions[layer] = None

    reality_position = layer_positions.get("reality")
    attention_position = layer_positions.get("attention")
    reality_attention_gap = (
        reality_position - attention_position
        if reality_position is not None and attention_position is not None
        else None
    )
    attention_overhang = (
        attention_position - reality_position
        if reality_position is not None and attention_position is not None
        else None
    )
    attention_excluding_main_values = [
        item["raw_score"]
        for item in layer_daily_raw_scores_excluding_main_page["attention"]
        if item["has_layer_events"]
    ]
    attention_excluding_main_sample_count = len(attention_excluding_main_values)
    if attention_excluding_main_sample_count >= MINIMUM_LAYER_SAMPLE_COUNT:
        attention_excluding_main_percentile, _, _, _ = percentile_rank(
            attention_excluding_main_values,
            target_layer_raw_scores_excluding_main_page["attention"],
        )
        attention_position_excluding_main_page = rounded_position(
            attention_excluding_main_percentile
        )
    else:
        attention_excluding_main_percentile = None
        attention_position_excluding_main_page = None
    reality_attention_gap_excluding_main_page = (
        reality_position - attention_position_excluding_main_page
        if reality_position is not None and attention_position_excluding_main_page is not None
        else None
    )
    attention_topic_page_values = [
        item["raw_score"]
        for item in layer_daily_raw_scores_topic_pages["attention"]
        if item["has_layer_events"]
    ]
    attention_topic_page_sample_count = len(attention_topic_page_values)
    if attention_topic_page_sample_count >= MINIMUM_LAYER_SAMPLE_COUNT:
        attention_topic_page_percentile, _, _, _ = percentile_rank(
            attention_topic_page_values,
            target_layer_raw_scores_topic_pages["attention"],
        )
        attention_position_topic_pages = rounded_position(attention_topic_page_percentile)
    else:
        attention_topic_page_percentile = None
        attention_position_topic_pages = None
    reality_attention_gap_topic_pages = (
        reality_position - attention_position_topic_pages
        if reality_position is not None and attention_position_topic_pages is not None
        else None
    )
    attention_targeted_values = [
        item["raw_score"]
        for item in layer_daily_raw_scores_targeted["attention"]
        if item["has_layer_events"]
    ]
    attention_targeted_sample_count = len(attention_targeted_values)
    if attention_targeted_sample_count >= MINIMUM_LAYER_SAMPLE_COUNT:
        attention_targeted_percentile, _, _, _ = percentile_rank(
            attention_targeted_values,
            target_layer_raw_scores_targeted["attention"],
        )
        attention_position_targeted = rounded_position(attention_targeted_percentile)
    else:
        attention_targeted_percentile = None
        attention_position_targeted = None
    reality_attention_gap_targeted = (
        reality_position - attention_position_targeted
        if reality_position is not None and attention_position_targeted is not None
        else None
    )
    attention_targeted_core_values = [
        item["raw_score"]
        for item in layer_daily_raw_scores_targeted_core["attention"]
        if item["has_layer_events"]
    ]
    attention_targeted_core_sample_count = len(attention_targeted_core_values)
    if attention_targeted_core_sample_count >= MINIMUM_LAYER_SAMPLE_COUNT:
        attention_targeted_core_percentile, _, _, _ = percentile_rank(
            attention_targeted_core_values,
            target_layer_raw_scores_targeted_core["attention"],
        )
        attention_position_targeted_core = rounded_position(
            attention_targeted_core_percentile
        )
    else:
        attention_targeted_core_percentile = None
        attention_position_targeted_core = None
    reality_attention_gap_targeted_core = (
        reality_position - attention_position_targeted_core
        if reality_position is not None and attention_position_targeted_core is not None
        else None
    )
    attention_targeted_context_values = [
        item["raw_score"]
        for item in layer_daily_raw_scores_targeted_context["attention"]
        if item["has_layer_events"]
    ]
    attention_targeted_context_sample_count = len(attention_targeted_context_values)
    if attention_targeted_context_sample_count >= MINIMUM_LAYER_SAMPLE_COUNT:
        attention_targeted_context_percentile, _, _, _ = percentile_rank(
            attention_targeted_context_values,
            target_layer_raw_scores_targeted_context["attention"],
        )
        attention_position_targeted_context = rounded_position(
            attention_targeted_context_percentile
        )
    else:
        attention_targeted_context_percentile = None
        attention_position_targeted_context = None
    reality_attention_gap_targeted_context = (
        reality_position - attention_position_targeted_context
        if reality_position is not None and attention_position_targeted_context is not None
        else None
    )

    return {
        "score_value": score_value,
        "raw_score": target_raw_score,
        "percentile_rank": percentile_value,
        "history_sample_count": sample_count,
        "less_count": less_count,
        "equal_count": equal_count,
        "daily_raw_scores": daily_raw_scores,
        "layer_daily_raw_scores": layer_daily_raw_scores,
        "layer_raw_scores": target_layer_raw_scores,
        "layer_positions": layer_positions,
        "layer_percentile_ranks": layer_percentile_ranks,
        "layer_sample_counts": layer_sample_counts,
        "layer_daily_raw_scores_excluding_main_page": (
            layer_daily_raw_scores_excluding_main_page
        ),
        "layer_raw_scores_excluding_main_page": (
            target_layer_raw_scores_excluding_main_page
        ),
        "layer_positions_excluding_main_page": {
            "attention": attention_position_excluding_main_page,
        },
        "layer_percentile_ranks_excluding_main_page": {
            "attention": attention_excluding_main_percentile,
        },
        "layer_sample_counts_excluding_main_page": {
            "attention": attention_excluding_main_sample_count,
        },
        "layer_gaps_excluding_main_page": {
            "reality_attention_gap": reality_attention_gap_excluding_main_page,
        },
        "layer_daily_raw_scores_topic_pages": layer_daily_raw_scores_topic_pages,
        "layer_raw_scores_topic_pages": target_layer_raw_scores_topic_pages,
        "layer_positions_topic_pages": {
            "attention": attention_position_topic_pages,
        },
        "layer_percentile_ranks_topic_pages": {
            "attention": attention_topic_page_percentile,
        },
        "layer_sample_counts_topic_pages": {
            "attention": attention_topic_page_sample_count,
        },
        "layer_gaps_topic_pages": {
            "reality_attention_gap": reality_attention_gap_topic_pages,
        },
        "layer_daily_raw_scores_targeted": layer_daily_raw_scores_targeted,
        "layer_raw_scores_targeted": target_layer_raw_scores_targeted,
        "layer_positions_targeted": {
            "attention": attention_position_targeted,
        },
        "layer_percentile_ranks_targeted": {
            "attention": attention_targeted_percentile,
        },
        "layer_sample_counts_targeted": {
            "attention": attention_targeted_sample_count,
        },
        "layer_gaps_targeted": {
            "reality_attention_gap": reality_attention_gap_targeted,
        },
        "layer_daily_raw_scores_targeted_core": layer_daily_raw_scores_targeted_core,
        "layer_raw_scores_targeted_core": target_layer_raw_scores_targeted_core,
        "layer_positions_targeted_core": {
            "attention": attention_position_targeted_core,
        },
        "layer_percentile_ranks_targeted_core": {
            "attention": attention_targeted_core_percentile,
        },
        "layer_sample_counts_targeted_core": {
            "attention": attention_targeted_core_sample_count,
        },
        "layer_gaps_targeted_core": {
            "reality_attention_gap": reality_attention_gap_targeted_core,
        },
        "layer_daily_raw_scores_targeted_context": (
            layer_daily_raw_scores_targeted_context
        ),
        "layer_raw_scores_targeted_context": target_layer_raw_scores_targeted_context,
        "layer_positions_targeted_context": {
            "attention": attention_position_targeted_context,
        },
        "layer_percentile_ranks_targeted_context": {
            "attention": attention_targeted_context_percentile,
        },
        "layer_sample_counts_targeted_context": {
            "attention": attention_targeted_context_sample_count,
        },
        "layer_gaps_targeted_context": {
            "reality_attention_gap": reality_attention_gap_targeted_context,
        },
        "attention_streams": {
            "global_topic": {
                "raw_score": target_layer_raw_scores_topic_pages["attention"],
                "position": attention_position_topic_pages,
            },
            "targeted": {
                "raw_score": target_layer_raw_scores_targeted["attention"],
                "position": attention_position_targeted,
                "matched_pages": target_targeted_matches,
            },
            "targeted_core": {
                "raw_score": target_layer_raw_scores_targeted_core["attention"],
                "position": attention_position_targeted_core,
                "matched_pages": target_targeted_core_matches,
            },
            "targeted_context": {
                "raw_score": target_layer_raw_scores_targeted_context["attention"],
                "position": attention_position_targeted_context,
                "matched_pages": target_targeted_context_matches,
            },
        },
        "layer_gaps": {
            "reality_attention_gap": reality_attention_gap,
            "attention_overhang": attention_overhang,
        },
        "context_event_count": context_event_count,
        "top_events": target_display_top_events,
        "scoring_top_events": target_scoring_top_events,
        "scored_events": target_scored_events,
        "positive_events": [
            event for event in events_by_date.get(target_date, []) if event["effective_anomaly"] > 0
        ],
        "window_start": window_start_date,
        "window_end": target_date,
    }


def json_ready_event(event):
    return {
        "id": str(event["id"]),
        "event_type": event["event_type"],
        "category": event["category"],
        "title": event["title"],
        "event_time": isoformat_z(event["event_time"]),
        "magnitude_value": float(event["magnitude_value"]) if event["magnitude_value"] is not None else None,
        "anomaly_score": float(event["anomaly_score"]),
        "effective_anomaly": event["effective_anomaly"],
        "layer": event.get("layer"),
    }


def build_component_scores(score_result, window_days):
    return {
        "raw_score": score_result["raw_score"],
        "percentile_rank": score_result["percentile_rank"],
        "history_sample_count": score_result["history_sample_count"],
        "window_days": window_days,
        "target_raw_score": score_result["raw_score"],
        "less_count": score_result["less_count"],
        "equal_count": score_result["equal_count"],
        "top_weights": TOP_WEIGHTS,
        "daily_raw_scores": score_result["daily_raw_scores"],
        "layer_raw_scores": score_result["layer_raw_scores"],
        "layer_positions": score_result["layer_positions"],
        "layer_percentile_ranks": score_result["layer_percentile_ranks"],
        "layer_sample_counts": score_result["layer_sample_counts"],
        "layer_gaps": score_result["layer_gaps"],
        "layer_daily_raw_scores": score_result["layer_daily_raw_scores"],
        "layer_raw_scores_excluding_main_page": (
            score_result["layer_raw_scores_excluding_main_page"]
        ),
        "layer_positions_excluding_main_page": (
            score_result["layer_positions_excluding_main_page"]
        ),
        "layer_percentile_ranks_excluding_main_page": (
            score_result["layer_percentile_ranks_excluding_main_page"]
        ),
        "layer_sample_counts_excluding_main_page": (
            score_result["layer_sample_counts_excluding_main_page"]
        ),
        "layer_gaps_excluding_main_page": (
            score_result["layer_gaps_excluding_main_page"]
        ),
        "layer_daily_raw_scores_excluding_main_page": (
            score_result["layer_daily_raw_scores_excluding_main_page"]
        ),
        "layer_raw_scores_topic_pages": score_result["layer_raw_scores_topic_pages"],
        "layer_positions_topic_pages": score_result["layer_positions_topic_pages"],
        "layer_percentile_ranks_topic_pages": (
            score_result["layer_percentile_ranks_topic_pages"]
        ),
        "layer_sample_counts_topic_pages": score_result["layer_sample_counts_topic_pages"],
        "layer_gaps_topic_pages": score_result["layer_gaps_topic_pages"],
        "layer_daily_raw_scores_topic_pages": (
            score_result["layer_daily_raw_scores_topic_pages"]
        ),
        "layer_raw_scores_targeted": score_result["layer_raw_scores_targeted"],
        "layer_positions_targeted": score_result["layer_positions_targeted"],
        "layer_percentile_ranks_targeted": (
            score_result["layer_percentile_ranks_targeted"]
        ),
        "layer_sample_counts_targeted": score_result["layer_sample_counts_targeted"],
        "layer_gaps_targeted": score_result["layer_gaps_targeted"],
        "layer_daily_raw_scores_targeted": (
            score_result["layer_daily_raw_scores_targeted"]
        ),
        "layer_raw_scores_targeted_core": (
            score_result["layer_raw_scores_targeted_core"]
        ),
        "layer_positions_targeted_core": (
            score_result["layer_positions_targeted_core"]
        ),
        "layer_percentile_ranks_targeted_core": (
            score_result["layer_percentile_ranks_targeted_core"]
        ),
        "layer_sample_counts_targeted_core": (
            score_result["layer_sample_counts_targeted_core"]
        ),
        "layer_gaps_targeted_core": score_result["layer_gaps_targeted_core"],
        "layer_daily_raw_scores_targeted_core": (
            score_result["layer_daily_raw_scores_targeted_core"]
        ),
        "layer_raw_scores_targeted_context": (
            score_result["layer_raw_scores_targeted_context"]
        ),
        "layer_positions_targeted_context": (
            score_result["layer_positions_targeted_context"]
        ),
        "layer_percentile_ranks_targeted_context": (
            score_result["layer_percentile_ranks_targeted_context"]
        ),
        "layer_sample_counts_targeted_context": (
            score_result["layer_sample_counts_targeted_context"]
        ),
        "layer_gaps_targeted_context": score_result["layer_gaps_targeted_context"],
        "layer_daily_raw_scores_targeted_context": (
            score_result["layer_daily_raw_scores_targeted_context"]
        ),
        "attention_streams": score_result["attention_streams"],
        "context_event_count": score_result["context_event_count"],
        "scoring_top_events": [
            json_ready_event(event) for event in score_result["scoring_top_events"]
        ],
        "excluded_top_signal_event_types": sorted(EXCLUDED_TOP_SIGNAL_EVENT_TYPES),
        "display_top_event_count": len(score_result["top_events"]),
        "scoring_top_event_count": len(score_result["scoring_top_events"]),
        "internal_layer_version_key": INTERNAL_LAYER_VERSION_KEY,
        "minimum_layer_sample_count": MINIMUM_LAYER_SAMPLE_COUNT,
    }


def build_explanation_payload(score_date, score_result, window_days):
    return {
        "score_version": VERSION_KEY,
        "data_date": score_date.isoformat(),
        "score_date": score_date.isoformat(),
        "raw_score": score_result["raw_score"],
        "percentile_rank": score_result["percentile_rank"],
        "history_sample_count": score_result["history_sample_count"],
        "window_days": window_days,
        "low_sample_count": score_result["history_sample_count"] < 3,
        "formula": FORMULA_TEXT,
        "score_value": score_result["score_value"],
        "layer_methodology": LAYER_METHODOLOGY,
        "layer_positions": score_result["layer_positions"],
        "layer_gaps": score_result["layer_gaps"],
        "layer_raw_scores": score_result["layer_raw_scores"],
        "layer_sample_counts": score_result["layer_sample_counts"],
        "layer_positions_excluding_main_page": (
            score_result["layer_positions_excluding_main_page"]
        ),
        "layer_gaps_excluding_main_page": (
            score_result["layer_gaps_excluding_main_page"]
        ),
        "layer_raw_scores_excluding_main_page": (
            score_result["layer_raw_scores_excluding_main_page"]
        ),
        "layer_positions_topic_pages": score_result["layer_positions_topic_pages"],
        "layer_gaps_topic_pages": score_result["layer_gaps_topic_pages"],
        "layer_raw_scores_topic_pages": score_result["layer_raw_scores_topic_pages"],
        "layer_positions_targeted": score_result["layer_positions_targeted"],
        "layer_gaps_targeted": score_result["layer_gaps_targeted"],
        "layer_raw_scores_targeted": score_result["layer_raw_scores_targeted"],
        "layer_positions_targeted_core": (
            score_result["layer_positions_targeted_core"]
        ),
        "layer_gaps_targeted_core": score_result["layer_gaps_targeted_core"],
        "layer_raw_scores_targeted_core": score_result["layer_raw_scores_targeted_core"],
        "layer_positions_targeted_context": (
            score_result["layer_positions_targeted_context"]
        ),
        "layer_gaps_targeted_context": score_result["layer_gaps_targeted_context"],
        "layer_raw_scores_targeted_context": (
            score_result["layer_raw_scores_targeted_context"]
        ),
        "attention_streams": score_result["attention_streams"],
        "topic_page_filtering_policy": {
            "excluded_titles": ["Main_Page"],
            "excluded_namespace_prefixes": list(NON_TOPIC_PAGE_PREFIXES),
            "empty_or_null_titles_excluded": True,
        },
        "targeted_attention_policy": {
            "match_policy": "normalized exact page title match",
            "targeted_attention_pages": TARGETED_ATTENTION_PAGES,
        },
        "top_events": [json_ready_event(event) for event in score_result["top_events"]],
        "scoring_top_events": [
            json_ready_event(event) for event in score_result["scoring_top_events"]
        ],
        "excluded_top_signal_event_types": sorted(EXCLUDED_TOP_SIGNAL_EVENT_TYPES),
        "principles": {
            "no_prediction": True,
            "no_fear_amplification": True,
            "no_trading_or_investment_advice": True,
        },
        "note": (
            "This score summarizes observed public signals for the selected data date. "
            "It is not a forecast, alert, or recommendation."
        ),
    }


def choose_json_column(columns):
    for column in JSON_COLUMNS:
        if column in columns:
            return column
    return None


def existing_score_exists(conn, columns, score_date):
    if not {"score_date", "score_version"}.issubset(columns):
        return False

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT 1
            FROM weirdness_scores
            WHERE score_date = %s
              AND score_version = %s
            LIMIT 1
            """,
            (score_date, VERSION_KEY),
        )
        return cur.fetchone() is not None


def assign_if_column(values, columns, column, value):
    if column in columns:
        values[column] = value


def build_score_values(columns, score_date, score_result, explanation_payload, component_scores):
    values = {}
    json_column = choose_json_column(columns)
    top_event_ids = [str(event["id"]) for event in score_result["top_events"]]

    assign_if_column(values, columns, "score_date", score_date)
    assign_if_column(values, columns, "score_value", score_result["score_value"])
    assign_if_column(values, columns, "score_version", VERSION_KEY)
    assign_if_column(values, columns, "top_event_ids", top_event_ids)
    assign_if_column(values, columns, "component_scores", Jsonb(component_scores))
    assign_if_column(values, columns, "calculated_at", datetime.now(timezone.utc))
    assign_if_column(values, columns, "created_at", datetime.now(timezone.utc))
    assign_if_column(values, columns, "updated_at", datetime.now(timezone.utc))

    if json_column is not None:
        values[json_column] = Jsonb(explanation_payload)

    return values


def save_weirdness_score(conn, columns, score_date, score_result, explanation_payload, component_scores):
    if not {"score_date", "score_version"}.issubset(columns):
        raise ValueError("weirdness_scores must include score_date and score_version")

    values = build_score_values(columns, score_date, score_result, explanation_payload, component_scores)
    exists = existing_score_exists(conn, columns, score_date)

    with conn.cursor() as cur:
        if exists:
            update_values = {
                column: value for column, value in values.items() if column != "created_at"
            }
            assignments = ", ".join(
                f"{column} = %s::uuid[]" if column == "top_event_ids" else f"{column} = %s"
                for column in update_values
            )
            if not assignments:
                return "skipped"
            cur.execute(
                f"""
                UPDATE weirdness_scores
                SET {assignments}
                WHERE score_date = %s
                  AND score_version = %s
                """,
                [*update_values.values(), score_date, VERSION_KEY],
            )
            return "updated"

        insert_columns = list(values)
        placeholders = ", ".join(
            "%s::uuid[]" if column == "top_event_ids" else "%s"
            for column in insert_columns
        )
        column_sql = ", ".join(insert_columns)
        cur.execute(
            f"""
            INSERT INTO weirdness_scores ({column_sql})
            VALUES ({placeholders})
            """,
            [values[column] for column in insert_columns],
        )
        return "inserted"


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Calculate World Pulse internal signal position score.")
    parser.add_argument(
        "--date",
        type=parse_date,
        default=None,
        help="Score date in YYYY-MM-DD format. Defaults to the latest observed UTC date.",
    )
    parser.add_argument(
        "--window-days",
        type=int,
        default=DEFAULT_WINDOW_DAYS,
        help="Percentile baseline window in days.",
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
    if args.window_days <= 0:
        print("--window-days must be greater than zero.", file=sys.stderr)
        return 2

    inserted = 0
    updated = 0
    errors = 0

    conn = None
    try:
        with psycopg.connect(args.database_url) as conn:
            score_version_columns = table_columns(conn, "score_versions")
            weirdness_columns = table_columns(conn, "weirdness_scores")
            if not score_version_columns:
                print("score_versions table was not found.", file=sys.stderr)
                return 1
            if not weirdness_columns:
                print("weirdness_scores table was not found.", file=sys.stderr)
                return 1

            ensure_score_version(conn, score_version_columns, args.window_days)
            score_date = args.date or latest_observation_date(conn)
            window_start = score_date - timedelta(days=args.window_days - 1)
            candidate_events = fetch_events_for_window(conn, window_start, score_date)
            score_result = calculate_window_scores(candidate_events, score_date, args.window_days)
            explanation_payload = build_explanation_payload(score_date, score_result, args.window_days)
            component_scores = build_component_scores(score_result, args.window_days)
            status = save_weirdness_score(
                conn,
                weirdness_columns,
                score_date,
                score_result,
                explanation_payload,
                component_scores,
            )
            if status == "inserted":
                inserted = 1
            elif status == "updated":
                updated = 1
            conn.commit()

    except Exception as exc:
        if conn is not None:
            conn.rollback()
        errors = 1
        score_date_text = args.date.isoformat() if args.date else "latest_observed"
        print(f"Signal Position calculation failed: score_date={score_date_text} error={exc}", file=sys.stderr)
        return 1

    print(
        "Signal Position calculation completed: "
        f"score_date={score_date.isoformat()} "
        f"candidate_events={len(candidate_events)} "
        f"scored_events={len(score_result['scored_events'])} "
        f"positive_events={len(score_result['positive_events'])} "
        f"top_events={len(score_result['top_events'])} "
        f"scoring_top_events={len(score_result['scoring_top_events'])} "
        f"raw_score={score_result['raw_score']:.4f} "
        f"percentile_rank={score_result['percentile_rank']:.2f} "
        f"score_value={score_result['score_value']} "
        f"inserted={inserted} "
        f"updated={updated} "
        f"errors={errors}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
