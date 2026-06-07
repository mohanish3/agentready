import json
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class PipelineStorageTests(unittest.TestCase):
    def test_pipeline_persists_scan_checks_run_and_research_sources(self):
        import pipeline

        events = [
            {
                "type": "check",
                "check": "llms.txt File",
                "key": "llms_txt",
                "status": "fail",
                "points_earned": 0,
                "points_max": 15,
                "points_lost": 15,
                "detail": "No llms.txt found.",
                "action": "Create /llms.txt.",
                "effort_level": "Easy",
                "effort_time": "1 hour",
                "research_source": {
                    "title": "The /llms.txt file",
                    "url": "https://llmstxt.org/",
                    "rationale": "Spec describes root /llms.txt Markdown structure.",
                    "last_reviewed": "2026-06-08",
                },
                "confidence": "high",
            },
            {
                "type": "complete",
                "url": "https://example.com",
                "score": 70,
                "checks": [
                    {
                        "check": "llms.txt File",
                        "key": "llms_txt",
                        "status": "fail",
                        "points_earned": 0,
                        "points_max": 15,
                        "points_lost": 15,
                        "detail": "No llms.txt found.",
                        "action": "Create /llms.txt.",
                        "effort_level": "Easy",
                        "effort_time": "1 hour",
                        "research_source": {
                            "title": "The /llms.txt file",
                            "url": "https://llmstxt.org/",
                            "rationale": "Spec describes root /llms.txt Markdown structure.",
                            "last_reviewed": "2026-06-08",
                        },
                        "confidence": "high",
                    }
                ],
                "recommendations": [],
                "subpages": {},
            },
        ]

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "agentready.sqlite3"
            with patch("pipeline.scan_stream", return_value=iter(events)):
                streamed = list(pipeline.scan_pipeline_stream("example.com", db_path=db_path))

            self.assertEqual(streamed[-1]["type"], "complete")
            self.assertEqual(streamed[-1]["scan_id"], 1)
            self.assertEqual(streamed[-1]["pipeline_run_id"], 1)

            with closing(sqlite3.connect(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                scan = conn.execute("select * from scans").fetchone()
                checks = conn.execute("select * from checks").fetchall()
                run = conn.execute("select * from pipeline_runs").fetchone()
                source = conn.execute("select * from research_sources where check_key = ?", ("llms_txt",)).fetchone()

                self.assertEqual(scan["url"], "https://example.com")
                self.assertEqual(scan["score"], 70)
                self.assertEqual(len(checks), 1)
                self.assertEqual(checks[0]["check_key"], "llms_txt")
                self.assertEqual(run["status"], "complete")
                self.assertEqual(source["url"], "https://llmstxt.org/")
                self.assertEqual(json.loads(scan["result_json"])["score"], 70)


if __name__ == "__main__":
    unittest.main()
