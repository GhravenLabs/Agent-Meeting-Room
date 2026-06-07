import os
import unittest
from unittest.mock import patch

import launcher


class LauncherTests(unittest.TestCase):
    def test_get_launcher_port_rejects_invalid_values(self):
        with patch.dict(os.environ, {"PORT": "bad-port"}):
            self.assertEqual(launcher.get_launcher_port(), launcher.DEFAULT_PORT)
        with patch.dict(os.environ, {"PORT": "70000"}):
            self.assertEqual(launcher.get_launcher_port(), launcher.DEFAULT_PORT)

    def test_get_launcher_port_accepts_valid_value(self):
        with patch.dict(os.environ, {"PORT": "5055"}):
            self.assertEqual(launcher.get_launcher_port(), 5055)

    def test_wait_for_server_returns_true_after_response(self):
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

        attempts = [OSError("not ready"), FakeResponse()]

        def fake_urlopen(*args, **kwargs):
            result = attempts.pop(0)
            if isinstance(result, Exception):
                raise result
            return result

        with (
            patch.object(launcher.request, "urlopen", side_effect=fake_urlopen),
            patch.object(launcher.time, "sleep"),
        ):
            self.assertTrue(launcher.wait_for_server("http://127.0.0.1:5000"))

    def test_open_browser_when_ready_skips_browser_when_server_never_starts(self):
        with (
            patch.object(launcher, "wait_for_server", return_value=False),
            patch.object(launcher.webbrowser, "open") as open_browser,
        ):
            self.assertFalse(launcher.open_browser_when_ready("http://127.0.0.1:5000"))

        open_browser.assert_not_called()


if __name__ == "__main__":
    unittest.main()
