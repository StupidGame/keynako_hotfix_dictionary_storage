import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
from apply_keynako_submission import SubmissionError, apply_submission  # type: ignore


class ApplyKeynakoSubmissionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "data_v1.json"
        self.path.write_text(
            json.dumps(
                {
                    "metadata": {
                        "status": "active",
                        "name": "data_v1.json",
                        "description": "test",
                        "version": "1.0",
                        "last_update": "2025-01-01T00:00:00+00:00",
                    },
                    "data": [],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        self.now = datetime(2026, 8, 28, 3, 4, 5, tzinfo=timezone.utc)

    def tearDown(self):
        self.directory.cleanup()

    def test_adds_importance_and_category_context(self):
        changed = apply_submission(
            self.path,
            {
                "word": "キーナコ",
                "ruby": "きーなこ",
                "importance": 5,
                "categories": ["場所・建物などの名前"],
            },
            now=self.now,
        )

        self.assertTrue(changed)
        document = json.loads(self.path.read_text(encoding="utf-8"))
        entry = document["data"][0]
        self.assertEqual(entry["importance"], 5)
        self.assertEqual(entry["word_weight"], -5.0)
        self.assertEqual(entry["lcid"], 1293)
        self.assertEqual(entry["author"], "Keynako app")
        self.assertEqual(document["metadata"]["version"], "1.1")
        self.assertEqual(document["metadata"]["last_update"], "2026-08-28T03:04:05+00:00")

    def test_updates_same_word_and_ruby_without_duplicate(self):
        base = {"word": "Keynako", "ruby": "きーなこ", "importance": 2}
        apply_submission(self.path, base, now=self.now)
        changed = apply_submission(self.path, {**base, "importance": 4}, now=self.now)

        self.assertTrue(changed)
        entries = json.loads(self.path.read_text(encoding="utf-8"))["data"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["importance"], 4)

    def test_consolidates_existing_duplicate_conversions(self):
        document = json.loads(self.path.read_text(encoding="utf-8"))
        document["data"] = [
            {
                "word": "Keynako",
                "ruby": "きーなこ",
                "word_weight": -15.0,
                "lcid": 1288,
                "rcid": 1288,
                "mid": 501,
                "date": "2025-01-01",
                "author": "first",
            },
            {
                "word": "別の変換",
                "ruby": "べつのへんかん",
                "word_weight": -15.0,
                "lcid": 1288,
                "rcid": 1288,
                "mid": 501,
                "date": "2025-01-01",
                "author": "test",
            },
            {
                "word": "Keynako",
                "ruby": "きーなこ",
                "word_weight": -10.0,
                "lcid": 1291,
                "rcid": 1291,
                "mid": 501,
                "date": "2025-01-02",
                "author": "second",
            },
        ]
        self.path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")

        changed = apply_submission(
            self.path,
            {
                "word": "Keynako",
                "ruby": "きーなこ",
                "importance": 4,
                "categories": ["人・動物・会社などの名前"],
            },
            now=self.now,
        )

        self.assertTrue(changed)
        entries = json.loads(self.path.read_text(encoding="utf-8"))["data"]
        matching = [
            entry
            for entry in entries
            if entry["word"] == "Keynako" and entry["ruby"] == "きーなこ"
        ]
        self.assertEqual(len(entries), 2)
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]["importance"], 4)
        self.assertEqual(matching[0]["author"], "Keynako app")

    def test_rejects_invalid_importance(self):
        with self.assertRaises(SubmissionError):
            apply_submission(
                self.path,
                {"word": "x", "ruby": "x", "importance": 6},
                now=self.now,
            )


if __name__ == "__main__":
    unittest.main()
