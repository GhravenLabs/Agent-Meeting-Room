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


if __name__ == "__main__":
    unittest.main()
