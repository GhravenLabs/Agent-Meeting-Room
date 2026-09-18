import unittest
from types import SimpleNamespace
from unittest.mock import patch

import app


class StatusExportEdges(unittest.TestCase):
    def test_ollama_health_rejects_http_errors(self):
        for status in (200, 204, 401, 404, 500):
            with self.subTest(status=status), patch.object(
                app.http_requests, "get", return_value=SimpleNamespace(status_code=status)
            ):
                self.assertEqual(app.check_ollama(), 200 <= status < 300)

    def test_cloud_status_ignores_blank_and_placeholder_keys(self):
        for value in (" ", "\t\n", "  your_api_key_here "):
            with self.subTest(value=value), patch.dict(
                app.os.environ, {"OPENAI_API_KEY": value}, clear=True
            ):
                self.assertFalse(app.cloud_agent_status()["codex"]["configured"])
        with patch.dict(app.os.environ, {"OPENAI_API_KEY": " actual-key "}, clear=True):
            self.assertTrue(app.cloud_agent_status()["codex"]["configured"])

    def test_transcript_titles_and_roles_stay_on_one_heading_line(self):
        with (
            patch.object(app, "load_config", return_value={"room": {"title": "Room\n# Extra"}}),
            patch.object(app, "conversation_history", [{"role": "Agent\r\n# Added", "content": "Hello"}]),
        ):
            transcript = app.build_transcript_markdown()
        self.assertIn("# Room Extra Transcript\n", transcript)
        self.assertIn("### 1. Agent Added\n", transcript)
        self.assertNotIn("\n Extra", transcript)
