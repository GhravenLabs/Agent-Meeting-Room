import tempfile
import unittest
from pathlib import Path

import customization


class CustomizationConfigTests(unittest.TestCase):
    def test_duration_is_clamped(self):
        self.assertEqual(customization.clamp_free_talk_duration(1), 60)
        self.assertEqual(customization.clamp_free_talk_duration(9999), 1800)
        self.assertEqual(customization.clamp_free_talk_duration("bad"), 300)

    def test_response_word_limit_is_clamped(self):
        self.assertEqual(customization.clamp_response_word_limit(10), 50)
        self.assertEqual(customization.clamp_response_word_limit(9999), 500)
        self.assertEqual(customization.clamp_response_word_limit("bad"), 150)

    def test_presets_only_keep_known_agent_keys(self):
        config = customization.normalize_config({
            "room": {"response_word_limit": 325},
            "presets": {
                "mixed": {
                    "name": "Mixed",
                    "description": "Contains one invalid key",
                    "agents": ["mistral", "missing-agent"],
                }
            }
        })

        self.assertEqual(config["room"]["response_word_limit"], 325)
        self.assertEqual(config["presets"]["mixed"]["agents"], ["mistral"])

    def test_default_templates_include_starter_prompts(self):
        config = customization.default_config()

        self.assertIn("@all review", config["presets"]["code_review"]["prompt"])
        self.assertIn("@debate product decision", config["presets"]["product_debate"]["prompt"])
        self.assertIn("@all research", config["presets"]["research"]["prompt"])
        self.assertIn("@all turn this goal", config["presets"]["planning"]["prompt"])

    def test_saved_default_preset_keeps_prompt_when_missing(self):
        config = customization.normalize_config({
            "presets": {
                "code_review": {
                    "name": "Code Review",
                    "description": "Old saved preset",
                    "agents": ["mistral"],
                }
            }
        })

        self.assertIn("@all review", config["presets"]["code_review"]["prompt"])

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
