import unittest

from deliverables import deliverable_options, generate_deliverable


class DeliverableTests(unittest.TestCase):
    def test_deliverable_options_include_pull_request(self):
        options = deliverable_options()

        self.assertIn(
            {"key": "pull_request", "label": "Pull Request Description"},
            options,
        )
        self.assertIn(
            {"key": "research_action_brief", "label": "Research Action Brief"},
            options,
        )

    def test_generate_deliverable_uses_recent_messages(self):
        markdown = generate_deliverable(
            "implementation_plan",
            [
                {"role": "user", "content": "We need searchable meeting notes."},
                {"role": "Codex", "content": "Add a small route and focused tests."},
            ],
            "Demo Room",
        )

        self.assertIn("# Implementation Plan", markdown)
        self.assertIn("- Room: Demo Room", markdown)
        self.assertIn("- Participants: user, Codex", markdown)
        self.assertIn("We need searchable meeting notes.", markdown)
        self.assertIn("Add a small route and focused tests.", markdown)

    def test_research_action_brief_turns_meeting_into_asset_plan(self):
        markdown = generate_deliverable(
            "research_action_brief",
            [
                {"role": "user", "content": "Use the website QA research for a better service demo."},
                {"role": "Codex", "content": "Turn it into an audit report and approval-gated outreach step."},
            ],
            "Webloom Planning",
        )

        self.assertIn("# Research Action Brief", markdown)
        self.assertIn("## Sellable Asset", markdown)
        self.assertIn("demo, report, SOP, checklist, lead list, or outreach script", markdown)
        self.assertIn("Do not send, publish, or deploy", markdown)

    def test_generate_deliverable_rejects_unknown_type(self):
        with self.assertRaises(ValueError):
            generate_deliverable("bad", [])


if __name__ == "__main__":
    unittest.main()
