#!/usr/bin/env python3
import json
import sys
from pathlib import Path

REQUIRED_METADATA_KEYS = {"status", "name", "description", "version", "last_update"}
REQUIRED_ENTRY_KEYS = {"word", "ruby", "word_weight", "lcid", "rcid", "mid", "date", "author"}


def validate(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
    except Exception as e:
        print(f"Failed to load JSON: {e}")
        return False

    if not isinstance(data, dict):
        print("Top level must be an object")
        return False

    if "metadata" not in data or "data" not in data:
        print("JSON must contain 'metadata' and 'data' keys")
        return False

    meta = data["metadata"]
    if not isinstance(meta, dict) or not REQUIRED_METADATA_KEYS.issubset(meta):
        print("'metadata' must contain keys: " + ", ".join(sorted(REQUIRED_METADATA_KEYS)))
        return False

    entries = data["data"]
    if not isinstance(entries, list):
        print("'data' must be a list")
        return False

    seen_conversions: dict[tuple[str, str], int] = {}
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            print(f"Entry {i} must be an object")
            return False
        missing = REQUIRED_ENTRY_KEYS - set(entry)
        if missing:
            print(f"Entry {i} missing keys: {', '.join(sorted(missing))}")
            return False
        word = entry["word"]
        ruby = entry["ruby"]
        if not isinstance(word, str) or not isinstance(ruby, str):
            print(f"Entry {i} word and ruby must be strings")
            return False
        conversion = (word, ruby)
        if conversion in seen_conversions:
            print(
                f"Entries {seen_conversions[conversion]} and {i} contain the same "
                f"conversion: {ruby} -> {word}"
            )
            return False
        seen_conversions[conversion] = i
        importance = entry.get("importance")
        if importance is not None and (
            isinstance(importance, bool)
            or not isinstance(importance, int)
            or importance not in range(1, 6)
        ):
            print(f"Entry {i} importance must be an integer from 1 to 5")
            return False
        categories = entry.get("categories")
        if categories is not None and (
            not isinstance(categories, list)
            or not all(isinstance(value, str) for value in categories)
        ):
            print(f"Entry {i} categories must be a list of strings")
            return False
    return True


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("Dictionary/data_v1.json")
    success = validate(path)
    if success:
        print("Validation succeeded")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
