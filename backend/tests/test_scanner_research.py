import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class ScannerResearchTests(unittest.TestCase):
    def test_each_check_has_research_source_metadata(self):
        import scanner

        check_keys = [key for key, _label, _points in scanner.CHECKS]
        self.assertEqual(set(check_keys), set(scanner.RESEARCH_SOURCES))

        for key in check_keys:
            source = scanner.RESEARCH_SOURCES[key]
            self.assertIn("title", source)
            self.assertTrue(source["url"].startswith("https://"))
            self.assertIn("rationale", source)
            self.assertRegex(source["last_reviewed"], r"^\d{4}-\d{2}-\d{2}$")

    def test_next_step_uses_highest_points_lost_recommendation(self):
        import scanner

        result = {
            "checks": [
                {"key": "contact_parsability", "status": "fail", "points_lost": 10},
                {"key": "structured_data", "status": "warning", "points_lost": 20},
            ],
            "recommendations": [
                {"key": "structured_data", "status": "warning", "points_lost": 20}
            ],
        }

        next_step = scanner._derive_next_step(result)
        self.assertEqual(next_step["key"], "structured_data")
        self.assertEqual(next_step["points_gain"], 20)
        self.assertIn("research_source", next_step)
        self.assertIn("workflow", next_step)


if __name__ == "__main__":
    unittest.main()
