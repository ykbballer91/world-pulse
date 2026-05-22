#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
from datetime import datetime


DEFAULT_TEXT_FILE = "public/share/world-pulse-latest.txt"
DEFAULT_IMAGE_FILE = "public/share/world-pulse-latest.jpg"
DEFAULT_POSTED_LOG = ".x_posted_dates.json"
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


def image_size(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"image file not found: {path}")
    size = os.path.getsize(path)
    if size <= 0:
        raise ValueError(f"image file is empty: {path}")
    return size


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


def build_summary(data_date, text, image_file, image_bytes, duplicate_post, would_post, reason):
    return {
        "data_date": data_date,
        "text_length": len(text),
        "image_file": image_file,
        "image_size_bytes": image_bytes,
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
        image_bytes = image_size(args.image_file)
        posted_log = load_posted_log(args.posted_log)
        duplicate_post = data_date in posted_log
        disallowed = find_disallowed(text)
        if disallowed:
            print("Post text contains disallowed terms.", file=sys.stderr)
            print(json.dumps({"data_date": data_date, "found_terms": disallowed}, indent=2), file=sys.stderr)
            return 1

        would_post = not duplicate_post
        reason = "ready" if would_post else "data date already exists in posted log"
        summary = build_summary(
            data_date=data_date,
            text=text,
            image_file=args.image_file,
            image_bytes=image_bytes,
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
