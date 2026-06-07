import os
import unittest
from unittest.mock import patch

import agents


class ClaudeAgentTests(unittest.TestCase):
    def test_ask_claude_reports_http_error(self):
        class FakeResponse:
            def raise_for_status(self):
                raise RuntimeError("401 Client Error")

            def json(self):
                raise AssertionError("json should not be parsed after HTTP error")

        with (
            patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}),
            patch.object(agents.requests, "post", return_value=FakeResponse()),
        ):
            result = agents.ask_claude("hello")

        self.assertIn("Claude error", result)
        self.assertIn("401 Client Error", result)


class CloudAgentTests(unittest.TestCase):
    def test_ask_codex_parses_output_text(self):
        class FakeResponse:
            def raise_for_status(self):
                return None

            def json(self):
                return {"output_text": "Implementation plan ready."}

        with (
            patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}),
            patch.object(agents.requests, "post", return_value=FakeResponse()) as post,
        ):
            result = agents.ask_codex("plan this")

        self.assertEqual(result, "Implementation plan ready.")
        self.assertEqual(post.call_args.kwargs["json"]["model"], agents.OPENAI_MODEL)

    def test_ask_gemini_accepts_google_api_key_alias(self):
        class FakeResponse:
            def raise_for_status(self):
                return None

            def json(self):
                return {
                    "candidates": [
                        {"content": {"parts": [{"text": "Option A\n"}, {"text": "Option B"}]}}
                    ]
                }

        with (
            patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}, clear=True),
            patch.object(agents.requests, "post", return_value=FakeResponse()) as post,
        ):
            result = agents.ask_gemini("compare this")

        self.assertEqual(result, "Option A\n\nOption B")
        self.assertEqual(post.call_args.kwargs["headers"]["X-Goog-Api-Key"], "test-key")

    def test_run_agents_routes_codex_mention(self):
        with patch.object(agents, "ask_codex", return_value="ship it") as ask_codex:
            responses = agents.run_agents("@codex make a plan", [], "")

        ask_codex.assert_called_once()
        self.assertEqual(responses[0]["agent"], "Codex")
        self.assertEqual(responses[0]["message"], "ship it")

    def test_run_agents_routes_google_alias_to_gemini(self):
        with patch.object(agents, "ask_gemini", return_value="three options") as ask_gemini:
            responses = agents.run_agents("@google compare options", [], "")

        ask_gemini.assert_called_once()
        self.assertEqual(responses[0]["agent"], "Gemini")
        self.assertEqual(responses[0]["message"], "three options")


if __name__ == "__main__":
    unittest.main()
