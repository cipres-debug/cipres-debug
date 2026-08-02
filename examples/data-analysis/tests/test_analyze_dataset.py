import json
import tempfile
import unittest
from pathlib import Path

from analyze_dataset import load_records, profile, render_svg


class AnalyzeDatasetTests(unittest.TestCase):
    def test_profile_numeric_and_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "rows.csv"
            source.write_text("name,score\nA,2\nB,\nC,4\n", encoding="utf-8")
            summary = profile(load_records(source))
        self.assertEqual(summary["row_count"], 3)
        self.assertEqual(summary["fields"]["score"]["kind"], "numeric")
        self.assertEqual(summary["fields"]["score"]["missing"], 1)
        self.assertEqual(summary["fields"]["score"]["mean"], 3)

    def test_json_wrapper_and_stable_columns(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "rows.json"
            source.write_text(json.dumps({"records": [{"b": "x", "a": 1}, {"a": 2}]}), encoding="utf-8")
            summary = profile(load_records(source))
        self.assertEqual(summary["columns"], ["a", "b"])
        self.assertEqual(summary["fields"]["b"]["top_values"], [{"value": "x", "count": 1}])

    def test_svg_contains_accessible_labels(self):
        svg = render_svg(profile([{"region": "north"}, {"region": "south"}, {"region": "north"}]))
        self.assertTrue(svg.startswith("<svg"))
        self.assertIn("Missing values by field", svg)
        self.assertIn("region", svg)

    def test_json_requires_objects(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "bad.json"
            source.write_text("[1, 2]", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "array of objects"):
                load_records(source)
