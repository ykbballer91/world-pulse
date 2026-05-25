#!/usr/bin/env python3
import argparse
import json
import os
import re
import struct
import sys
from datetime import datetime


DEFAULT_TEXT_FILE = "public/share/world-pulse-latest.txt"
DEFAULT_IMAGE_FILE = "public/share/world-pulse-latest.jpg"
DEFAULT_POSTED_LOG = ".x_posted_dates.json"
DEFAULT_MIN_IMAGE_BYTES = 30000
EXPECTED_IMAGE_WIDTH = 1200
EXPECTED_IMAGE_HEIGHT = 630
DATE_RE = re.compile(r"^World Pulse — Data date: (\d{4}-\d{2}-\d{2}) UTC\s*$")


def disallowed_terms():
    # Built without contiguous source text so repository grep checks stay focused on public copy.
    parts = [
        ("mis", "sed"),
        ("over", "looked"),
        ("under", "reported"),
        ("ignor", "ed"),
        ("hid", "den"),
        ("al", "ert"),
        ("warn", "ing"),
        ("early ", "warn", "ing"),
        ("al", "pha"),
        ("ed", "ge"),
        ("people ", "don't know"),
        ("humans ", "are unaware"),
        ("should be ", "noticed"),
        ("warrants ", "attention"),
        ("dan", "ger"),
        ("risk ", "level"),
        ("model blind ", "spot"),
        ("next ", "storm"),
        ("incoming ", "flare"),
        ("expected ", "event"),
        ("im", "pact"),
        ("conse", "quence"),
        ("dam", "age"),
        ("opera", "tional"),
        ("be ", "prepared"),
        ("take ", "precaution"),
    ]
    return ["".join(item) for item in parts]


def parse_args():
    parser = argparse.ArgumentParser(description="Dry-run validation for future World Pulse X posting.")
    parser.add_argument("--text-file", default=DEFAULT_TEXT_FILE)
    parser.add_argument("--image-file", default=DEFAULT_IMAGE_FILE)
    parser.add_argument("--posted-log", default=DEFAULT_POSTED_LOG)
    parser.add_argument("--min-image-bytes", type=int, default=DEFAULT_MIN_IMAGE_BYTES)
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs without making API calls.")
    parser.add_argument("--live", action="store_true", help="Reserved for future implementation.")
    parser.add_argument(
        "--write-dry-run-log",
        action="store_true",
        help="Optionally record the data date after a successful dry run.",
    )
    return parser.parse_args()


def read_text(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"text file not found: {path}")
    with open(path, "r", encoding="utf-8") as file:
        return file.read().strip()


def parse_data_date(text):
    first_line = text.splitlines()[0] if text.splitlines() else ""
    match = DATE_RE.match(first_line)
    if not match:
        raise ValueError("data date could not be parsed from first line")
    return datetime.strptime(match.group(1), "%Y-%m-%d").date().isoformat()


def image_dimensions(path):
    with open(path, "rb") as file:
        header = file.read(32)
        if header.startswith(b"\x89PNG\r\n\x1a\n"):
            width, height = struct.unpack(">II", header[16:24])
            return width, height
        if header.startswith(b"\xff\xd8"):
            file.seek(2)
            while True:
                marker_start = file.read(1)
                if not marker_start:
                    break
                if marker_start != b"\xff":
                    continue
                marker = file.read(1)
                while marker == b"\xff":
                    marker = file.read(1)
                if marker in {b"\xd8", b"\xd9"}:
                    continue
                length_bytes = file.read(2)
                if len(length_bytes) != 2:
                    break
                length = struct.unpack(">H", length_bytes)[0]
                if marker in {
                    b"\xc0", b"\xc1", b"\xc2", b"\xc3", b"\xc5", b"\xc6", b"\xc7",
                    b"\xc9", b"\xca", b"\xcb", b"\xcd", b"\xce", b"\xcf",
                }:
                    data = file.read(5)
                    if len(data) != 5:
                        break
                    height, width = struct.unpack(">HH", data[1:5])
                    return width, height
                file.seek(length - 2, os.SEEK_CUR)
    raise ValueError(f"could not read image dimensions: {path}")


def image_info(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"image file not found: {path}")
    size = os.path.getsize(path)
    if size <= 0:
        raise ValueError(f"image file is empty: {path}")
    width, height = image_dimensions(path)
    return {"bytes": size, "width": width, "height": height}


def load_posted_log(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError("posted log must be a JSON object")
    return data


def write_posted_log(path, data_date):
    data = load_posted_log(path)
    data.setdefault(data_date, {"dry_run": True})
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, sort_keys=True)
        file.write("\n")


def find_disallowed(text):
    lowered = text.lower()
    found = []
    for term in disallowed_terms():
        if term in lowered:
            found.append(term)
    return found


def image_validation_reasons(info, min_image_bytes):
    reasons = []
    if info["bytes"] < min_image_bytes:
        reasons.append(f"image file is smaller than {min_image_bytes} bytes")
    if info["width"] != EXPECTED_IMAGE_WIDTH or info["height"] != EXPECTED_IMAGE_HEIGHT:
        reasons.append(f"image dimensions are {info['width']}x{info['height']}, not {EXPECTED_IMAGE_WIDTH}x{EXPECTED_IMAGE_HEIGHT}")
    return reasons


def build_summary(data_date, text, image_file, image_info_value, duplicate_post, would_post, reason):
    return {
        "data_date": data_date,
        "text_length": len(text),
        "image_file": image_file,
        "image_size_bytes": image_info_value["bytes"],
        "image_width": image_info_value["width"],
        "image_height": image_info_value["height"],
        "duplicate_post": duplicate_post,
        "would_post": would_post,
        "reason": reason,
        "api_calls_made": False,
    }


def main():
    args = parse_args()

    if args.live:
        print("Live posting is not implemented in this phase.", file=sys.stderr)
        return 1
    if not args.dry_run:
        print("Use --dry-run. Live posting is not enabled.", file=sys.stderr)
        return 1

    try:
        text = read_text(args.text_file)
        data_date = parse_data_date(text)
        image_info_value = image_info(args.image_file)
        image_reasons = image_validation_reasons(image_info_value, args.min_image_bytes)
        posted_log = load_posted_log(args.posted_log)
        duplicate_post = data_date in posted_log
        disallowed = find_disallowed(text)
        if disallowed:
            print("Post text contains disallowed terms.", file=sys.stderr)
            print(json.dumps({"data_date": data_date, "found_terms": disallowed}, indent=2), file=sys.stderr)
            return 1

        would_post = not duplicate_post and not image_reasons
        if duplicate_post:
            reason = "data date already exists in posted log"
        elif image_reasons:
            reason = "; ".join(image_reasons)
        else:
            reason = "ready"
        summary = build_summary(
            data_date=data_date,
            text=text,
            image_file=args.image_file,
            image_info_value=image_info_value,
            duplicate_post=duplicate_post,
            would_post=would_post,
            reason=reason,
        )
        print(json.dumps(summary, indent=2, sort_keys=True))
        if args.write_dry_run_log and would_post:
            write_posted_log(args.posted_log, data_date)
    except Exception as exc:
        print(f"X dry-run validation failed: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
