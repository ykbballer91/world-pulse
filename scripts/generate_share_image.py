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
EXCLUDED_TOP_SIGNAL_EVENT_TYPES = {
    "wikipedia_attention_snapshot",
}


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


FONT_SELECTION = {
    "regular": None,
    "bold": None,
    "fallback_used": False,
}


def font_candidates(bold=False):
    regular_candidates = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    bold_candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ]
    return bold_candidates if bold else regular_candidates


def load_font(size, bold=False):
    key = "bold" if bold else "regular"
    selected_path = FONT_SELECTION[key]
    if selected_path:
        return ImageFont.truetype(selected_path, size)

    for path in font_candidates(bold):
        if os.path.exists(path):
            FONT_SELECTION[key] = path
            return ImageFont.truetype(path, size)

    FONT_SELECTION["fallback_used"] = True
    return ImageFont.load_default()


def validate_font_selection():
    if FONT_SELECTION["fallback_used"] or not FONT_SELECTION["regular"] or not FONT_SELECTION["bold"]:
        raise RuntimeError(
            "Share image font fallback used; install DejaVuSans or LiberationSans on the runner."
        )


def font_log_line():
    return (
        "Share image font selection: "
        f"regular={FONT_SELECTION['regular']} "
        f"bold={FONT_SELECTION['bold']} "
        f"fallback_used={str(FONT_SELECTION['fallback_used']).lower()}"
    )


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
    top_cards = [
        card
        for card in top_cards
        if card.get("event_type") not in EXCLUDED_TOP_SIGNAL_EVENT_TYPES
    ]
    contributors = [
        card for card in top_cards if card.get("signal_status") == "score_contributor"
    ]
    if contributors:
        return contributors[0]
    return top_cards[0] if top_cards else None


def score_band_label(score):
    if score <= 20:
        return "Lower-range position"
    if score <= 50:
        return "Mid-range position"
    if score <= 80:
        return "Upper-range position"
    return "High-range position"


def format_signed(value):
    if value is None:
        return "n/a"
    return f"{float(value):+.2f}".replace(". ", ".").replace(" .", ".")


def format_plain(value):
    if value is None:
        return "n/a"
    return f"{float(value):.2f}".replace(". ", ".").replace(" .", ".")



def generate_image(display_date, page_payload):
    image = Image.new("RGB", (WIDTH, HEIGHT), "#F7F7F4")
    draw = ImageDraw.Draw(image)

    font_brand = load_font(30, bold=True)
    font_headline = load_font(54, bold=True)
    font_hero = load_font(104, bold=True)
    font_body = load_font(26)
    font_small = load_font(20)
    font_footer = load_font(20)
    font_label = load_font(21, bold=True)
    font_card_title = load_font(25, bold=True)

    ink = "#171717"
    muted = "#5f5f5f"
    light = "#d8d8d5"
    softer = "#efefec"
    footer = "#62625d"

    score = int(page_payload.get("signal_position", page_payload.get("weirdness_score", 0)))
    card = top_contributor(page_payload.get("top_cards", []))
    signal_title = card.get("title") if card else "No individual top signal for this data date"
    # Keep the share image intentionally low-detail to avoid score misinterpretation.

    draw.text((72, 58), f"World Pulse — Data date: {display_date.isoformat()} UTC", font=font_brand, fill=ink)
    draw.text((72, 150), "Signal Position", font=font_headline, fill=ink)
    draw.text((72, 228), f"{score} / 100", font=font_hero, fill=ink)
    draw.text((72, 350), "Position within the last 30 observed days.", font=font_body, fill=muted)
    draw.text((72, 398), "Not a forecast or emergency notice.", font=font_body, fill=muted)
    draw.text((72, 445), score_band_label(score), font=font_body, fill=ink)

    card_left = 744
    card_top = 360
    card_right = 1128
    card_bottom = 552
    content_left = 770
    draw.rounded_rectangle(
        (card_left, card_top, card_right, card_bottom),
        radius=16,
        outline=light,
        width=2,
        fill="#ffffff",
    )
    draw.text((content_left, card_top + 24), "Top signal", font=font_label, fill=muted)
    draw_wrapped(draw, (content_left, card_top + 58), signal_title, font_card_title, ink, 320, line_spacing=8, max_lines=2)

    if card:
        pill_left = content_left
        pill_top = card_top + 124
        pill_right = pill_left + 166
        pill_bottom = pill_top + 34
        draw.rounded_rectangle((pill_left, pill_top, pill_right, pill_bottom), radius=21, fill=softer)
        draw.text((pill_left + 16, pill_top + 7), "Observed signal", font=font_small, fill=ink)

    draw.text((72, 568), "worldpulse.today", font=font_footer, fill=footer)
    validate_font_selection()
    return image


def save_images(image, display_date):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    dated_png_path = os.path.join(OUTPUT_DIR, f"world-pulse-{display_date.isoformat()}.png")
    latest_png_path = os.path.join(OUTPUT_DIR, "world-pulse-latest.png")
    dated_jpg_path = os.path.join(OUTPUT_DIR, f"world-pulse-{display_date.isoformat()}.jpg")
    latest_jpg_path = os.path.join(OUTPUT_DIR, "world-pulse-latest.jpg")

    image.save(dated_png_path, "PNG")
    image.save(latest_png_path, "PNG")

    jpg_image = image.convert("RGB")
    jpg_image.save(dated_jpg_path, "JPEG", quality=92, optimize=True)
    jpg_image.save(latest_jpg_path, "JPEG", quality=92, optimize=True)

    return dated_png_path, latest_png_path, dated_jpg_path, latest_jpg_path


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
        print(font_log_line())
        dated_png_path, latest_png_path, dated_jpg_path, latest_jpg_path = save_images(image, display_date)
    except Exception as exc:
        print(f"Share image generation failed: {exc}", file=sys.stderr)
        return 1

    print(
        "Generated share image: "
        f"display_date={display_date.isoformat()} "
        f"png={os.path.relpath(dated_png_path, ROOT_DIR)} "
        f"latest_png={os.path.relpath(latest_png_path, ROOT_DIR)} "
        f"jpg={os.path.relpath(dated_jpg_path, ROOT_DIR)} "
        f"latest_jpg={os.path.relpath(latest_jpg_path, ROOT_DIR)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
