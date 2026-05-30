import tempfile
import unittest
from pathlib import Path

import customization


class CustomizationConfigTests(unittest.TestCase):
    def test_duration_is_clamped(self):
        self.assertEqual(customization.clamp_free_talk_duration(1), 60)
        self.assertEqual(customization.clamp_free_talk_duration(9999), 1800)
        self.assertEqual(customization.clamp_free_talk_duration("bad"), 300)

    def test_presets_only_keep_known_agent_keys(self):
        config = customization.normalize_config({
            "presets": {
                "mixed": {
                    "name": "Mixed",
                    "description": "Contains one invalid key",
                    "agents": ["mistral", "missing-agent"],
                }
            }
        })

        self.assertEqual(config["presets"]["mixed"]["agents"], ["mistral"])

    def test_save_and_load_round_trips_custom_agent_profile(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original_path = customization.CONFIG_PATH
            customization.CONFIG_PATH = Path(tmpdir) / "agent_profiles.json"
            try:
                config = customization.default_config()
                config["agents"]["mistral"]["display_name"] = "Careful Mistral"
                config["agents"]["mistral"]["role"] = "Reviewer"

                customization.save_config(config)
                loaded = customization.load_config()

                self.assertEqual(
                    loaded["agents"]["mistral"]["display_name"],
                    "Careful Mistral",
                )
                self.assertEqual(loaded["agents"]["mistral"]["role"], "Reviewer")
            finally:
                customization.CONFIG_PATH = original_path


if __name__ == "__main__":
    unittest.main()
