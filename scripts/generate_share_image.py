#!/usr/bin/env python3
import argparse
import os
import sys
from datetime import datetime

import psycopg
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(ROOT_DIR, "public", "share")
WIDTH = 1200
HEIGHT = 630
PAYLOAD_COLUMNS = ["page_payload", "display_payload", "payload", "metadata"]


def parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--date must use YYYY-MM-DD format") from exc


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


def choose_payload_column(columns):
    for column in PAYLOAD_COLUMNS:
        if column in columns:
            return column
    raise ValueError("display_log must include a page payload JSON column")


def latest_display_date(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT display_date
            FROM display_log
            ORDER BY display_date DESC
            LIMIT 1
            """
        )
        row = cur.fetchone()
        if row is None:
            raise ValueError("no display_log rows were found")
        return row[0]


def fetch_display_payload(conn, display_date):
    columns = table_columns(conn, "display_log")
    if not columns:
        raise ValueError("display_log table was not found")
    if "display_date" not in columns:
        raise ValueError("display_log must include display_date")

    payload_column = choose_payload_column(columns)
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT display_date, {payload_column}
            FROM display_log
            WHERE display_date = %s
            LIMIT 1
            """,
            (display_date,),
        )
        row = cur.fetchone()
        if row is None:
            raise ValueError(f"display payload not found for date: {display_date.isoformat()}")
        return row


def load_font(size, bold=False):
    regular_candidates = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
    ]
    bold_candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial Bold.ttf",
    ]
    for path in bold_candidates if bold else regular_candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def wrap_text(draw, text, font, max_width):
    words = str(text).split()
    lines = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def draw_wrapped(draw, xy, text, font, fill, max_width, line_spacing=8, max_lines=None):
    x, y = xy
    lines = wrap_text(draw, text, font, max_width)
    if max_lines is not None:
        lines = lines[:max_lines]
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        bbox = draw.textbbox((x, y), line, font=font)
        y += (bbox[3] - bbox[1]) + line_spacing
    return y


def top_contributor(top_cards):
    contributors = [
        card for card in top_cards if card.get("signal_status") == "score_contributor"
    ]
    if contributors:
        return contributors[0]
    return top_cards[0] if top_cards else None


def score_band_label(score):
    if score <= 20:
        return "Near baseline"
    if score <= 50:
        return "Moderately above baseline"
    if score <= 80:
        return "Clearly above baseline"
    return "Unusually elevated"


def status_label(card):
    if not card:
        return "Context only"
    return "Above baseline" if card.get("signal_status") == "score_contributor" else "Context only"


def format_signed(value):
    if value is None:
        return "n/a"
    return f"{float(value):+.2f}".replace(". ", ".").replace(" .", ".")


def format_plain(value):
    if value is None:
        return "n/a"
    return f"{float(value):.2f}".replace(". ", ".").replace(" .", ".")


def compact_percentile_line(page_payload):
    line = page_payload.get("percentile_line")
    if not line:
        summary_lines = page_payload.get("summary_lines", [])
        line = summary_lines[0] if summary_lines else None
    if not line:
        return None
    line = line.replace("This data date is in the ", "")
    line = line.replace("of the last ", "of last ")
    line = line.rstrip(".")
    return line


def generate_image(display_date, page_payload):
    image = Image.new("RGB", (WIDTH, HEIGHT), "#F7F7F4")
    draw = ImageDraw.Draw(image)

    font_brand = load_font(30, bold=True)
    font_date = load_font(24)
    font_headline = load_font(44, bold=True)
    font_score = load_font(190, bold=True)
    font_band = load_font(30, bold=True)
    font_body = load_font(27)
    font_small = load_font(21)
    font_footer = load_font(18)
    font_label = load_font(24, bold=True)
    font_card_title = load_font(34, bold=True)

    ink = "#171717"
    muted = "#5f5f5f"
    light = "#d8d8d5"
    softer = "#efefec"
    footer = "#74746f"

    score = int(page_payload.get("weirdness_score", 0))
    card = top_contributor(page_payload.get("top_cards", []))
    signal_title = card.get("title") if card else "No top signal available"
    anomaly = card.get("anomaly_score") if card else None
    contribution = card.get("score_contribution") if card else None
    anomaly_text = f"Anomaly {format_signed(anomaly)}σ".replace(". ", ".").replace(" .", ".")
    contribution_text = f"Contribution {format_plain(contribution)}".replace(". ", ".").replace(" .", ".")

    draw.text((72, 58), "World Pulse", font=font_brand, fill=ink)
    draw.text((72, 102), f"Data date: {display_date.isoformat()}", font=font_date, fill=muted)

    draw.text((72, 196), "Latest Weirdness Score", font=font_headline, fill=ink)
    draw.text((68, 248), str(score), font=font_score, fill=ink)
    draw.text((78, 452), score_band_label(score), font=font_band, fill=ink)

    percentile_line = compact_percentile_line(page_payload)
    if percentile_line:
        draw_wrapped(draw, (78, 500), percentile_line, font_small, muted, 470, line_spacing=6, max_lines=1)

    card_left = 610
    card_top = 238
    card_right = 1128
    card_bottom = 548
    content_left = 650
    draw.rounded_rectangle(
        (card_left, card_top, card_right, card_bottom),
        radius=18,
        outline=light,
        width=2,
        fill="#ffffff",
    )
    draw.text((content_left, card_top + 30), "Top signal", font=font_label, fill=muted)
    draw_wrapped(
        draw,
        (content_left, card_top + 70),
        signal_title,
        font_card_title,
        ink,
        420,
        line_spacing=10,
        max_lines=3,
    )

    pill_left = content_left
    pill_top = card_top + 174
    pill_right = pill_left + 176
    pill_bottom = pill_top + 42
    draw.rounded_rectangle((pill_left, pill_top, pill_right, pill_bottom), radius=21, fill=softer)
    draw.text((pill_left + 20, pill_top + 10), status_label(card), font=font_small, fill=ink)

    draw.text((content_left, card_top + 236), anomaly_text, font=font_body, fill=ink)
    draw.text((content_left, card_top + 274), contribution_text, font=font_body, fill=ink)

    draw.text((72, 552), "Not a forecast, alert, or recommendation.", font=font_footer, fill=footer)
    draw.text((72, 578), "Public observation and attention data.", font=font_footer, fill=footer)
    return image


def save_images(image, display_date):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    dated_path = os.path.join(OUTPUT_DIR, f"world-pulse-{display_date.isoformat()}.png")
    latest_path = os.path.join(OUTPUT_DIR, "world-pulse-latest.png")
    image.save(dated_path, "PNG")
    image.save(latest_path, "PNG")
    return dated_path, latest_path


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Generate World Pulse share image.")
    parser.add_argument(
        "--date",
        type=parse_date,
        default=None,
        help="Display date in YYYY-MM-DD format. Defaults to latest display_log date.",
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

    try:
        with psycopg.connect(args.database_url) as conn:
            display_date = args.date or latest_display_date(conn)
            display_date, page_payload = fetch_display_payload(conn, display_date)
        image = generate_image(display_date, page_payload)
        dated_path, latest_path = save_images(image, display_date)
    except Exception as exc:
        print(f"Share image generation failed: {exc}", file=sys.stderr)
        return 1

    print(
        "Generated share image: "
        f"display_date={display_date.isoformat()} "
        f"output={os.path.relpath(dated_path, ROOT_DIR)} "
        f"latest={os.path.relpath(latest_path, ROOT_DIR)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
