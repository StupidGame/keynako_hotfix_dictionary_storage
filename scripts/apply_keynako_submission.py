#!/usr/bin/env python3
"""Validate and apply one Keynako app submission to data_v1.json."""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CONTROL_CHARACTERS = re.compile(r"[\x00-\x1f\x7f]")
CATEGORY_IDS = {
    "人・動物・会社などの名前": 1291,
    "場所・建物などの名前": 1293,
}


class SubmissionError(ValueError):
    """Raised when an app submission cannot safely enter the dictionary."""


def _clean_text(payload: dict[str, Any], key: str, maximum: int) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise SubmissionError(f"{key} must be a string")
    value = value.strip()
    if not value or len(value) > maximum or CONTROL_CHARACTERS.search(value):
        raise SubmissionError(f"{key} is empty, too long, or contains control characters")
    return value


def normalize_submission(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise SubmissionError("payload must be an object")
    word = _clean_text(payload, "word", 128)
    ruby = _clean_text(payload, "ruby", 256)
    importance = payload.get("importance")
    if isinstance(importance, bool) or not isinstance(importance, int) or importance not in range(1, 6):
        raise SubmissionError("importance must be an integer from 1 to 5")

    raw_categories = payload.get("categories", [])
    if not isinstance(raw_categories, list) or len(raw_categories) > 10:
        raise SubmissionError("categories must be a list with at most 10 values")
    categories: list[str] = []
    for value in raw_categories:
        if not isinstance(value, str) or len(value) > 64 or CONTROL_CHARACTERS.search(value):
            raise SubmissionError("category values must be short strings")
        if value and value not in categories:
            categories.append(value)

    note = payload.get("note")
    if note is not None:
        if not isinstance(note, str) or len(note) > 1000 or CONTROL_CHARACTERS.search(note):
            raise SubmissionError("note must be a string no longer than 1000 characters")
        note = note.strip()

    return {
        "word": word,
        "ruby": ruby,
        "importance": importance,
        "categories": categories,
        "note": note,
    }


def apply_submission(
    dictionary_path: Path,
    payload: Any,
    *,
    now: datetime | None = None,
) -> bool:
    submission = normalize_submission(payload)
    document = json.loads(dictionary_path.read_text(encoding="utf-8"))
    entries = document.get("data")
    metadata = document.get("metadata")
    if not isinstance(entries, list) or not isinstance(metadata, dict):
        raise SubmissionError("dictionary has an invalid top-level structure")

    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    categories = submission["categories"]
    context_id = next((CATEGORY_IDS[value] for value in categories if value in CATEGORY_IDS), 1288)
    importance = submission["importance"]
    entry = {
        "word": submission["word"],
        "ruby": submission["ruby"],
        "word_weight": -17.5 + 2.5 * importance,
        "importance": importance,
        "lcid": context_id,
        "rcid": context_id,
        "mid": 501,
        "date": current.date().isoformat(),
        "author": "Keynako app",
        "categories": categories,
    }
    if submission["note"]:
        entry["note"] = submission["note"]

    existing = next(
        (
            value
            for value in entries
            if isinstance(value, dict)
            and value.get("word") == entry["word"]
            and value.get("ruby") == entry["ruby"]
        ),
        None,
    )
    if existing == entry:
        return False
    if existing is None:
        entries.append(entry)
    else:
        existing.clear()
        existing.update(entry)

    metadata["version"] = "1.1"
    metadata["last_update"] = current.isoformat(timespec="seconds")
    rendered = json.dumps(document, ensure_ascii=False, indent=4) + "\n"
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{dictionary_path.name}.",
        dir=dictionary_path.parent,
        text=True,
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as temporary:
            temporary.write(rendered)
        Path(temporary_name).replace(dictionary_path)
    except Exception:
        Path(temporary_name).unlink(missing_ok=True)
        raise
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dictionary",
        type=Path,
        default=Path("Dictionary/data_v1.json"),
    )
    parser.add_argument("--payload-json", required=True)
    args = parser.parse_args()
    changed = apply_submission(args.dictionary, json.loads(args.payload_json))
    print("Dictionary updated" if changed else "Submission already matches dictionary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
