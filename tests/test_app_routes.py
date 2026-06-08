import unittest
from unittest.mock import patch

import app as app_module


class AppRouteTests(unittest.TestCase):
    def setUp(self):
        self.client = app_module.app.test_client()
        app_module.conversation_history.clear()

    def test_chat_rejects_missing_message(self):
        response = self.client.post("/chat", json={})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["error"], "empty message")

    def test_get_port_rejects_invalid_values(self):
        with patch.dict(app_module.os.environ, {"PORT": "70000"}):
            self.assertEqual(app_module.get_port(), 5000)
        with patch.dict(app_module.os.environ, {"PORT": "not-a-port"}):
            self.assertEqual(app_module.get_port(), 5000)

    def test_check_ollama_models_skips_malformed_entries(self):
        class FakeResponse:
            status_code = 200

            def json(self):
                return {"models": [{"name": "mistral"}, {}, "bad", {"name": ""}]}

        with patch.object(app_module.http_requests, "get", return_value=FakeResponse()):
            self.assertEqual(app_module.check_ollama_models(), ["mistral"])

    def test_status_reports_cloud_agent_configuration(self):
        with (
            patch.dict(app_module.os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True),
            patch.object(app_module, "check_ollama", return_value=False),
        ):
            response = self.client.get("/status")

        self.assertEqual(response.status_code, 200)
        cloud_agents = response.json["cloud_agents"]
        self.assertFalse(cloud_agents["claude"]["configured"])
        self.assertTrue(cloud_agents["codex"]["configured"])
        self.assertFalse(cloud_agents["gemini"]["configured"])
        self.assertEqual(response.json["claude"]["configured"], cloud_agents["claude"]["configured"])

    def test_chat_uses_agent_runner(self):
        original = app_module.run_agents
        app_module.run_agents = lambda message, history, memory: [{
            "agent": "TestAgent",
            "message": f"Echo: {message}",
        }]
        try:
            response = self.client.post("/chat", json={"message": "@all hello"})
        finally:
            app_module.run_agents = original

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["responses"][0]["message"], "Echo: @all hello")

    def test_chat_history_trims_bulk_responses_to_limit(self):
        original = app_module.run_agents
        app_module.conversation_history.extend(
            {"role": "agent", "content": str(index)} for index in range(49)
        )
        app_module.run_agents = lambda message, history, memory: [
            {"agent": f"Agent{index}", "message": "ok"} for index in range(5)
        ]
        try:
            response = self.client.post("/chat", json={"message": "@all hello"})
        finally:
            app_module.run_agents = original

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(app_module.conversation_history), app_module.MAX_CONVERSATION_HISTORY)

    def test_talk_rejects_missing_topic(self):
        response = self.client.post("/talk", json={})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["error"], "no topic")

    def test_talk_clamps_duration(self):
        original = app_module.run_free_talk_thread
        app_module.run_free_talk_thread = lambda *args, **kwargs: args[2].put(None)
        try:
            response = self.client.post("/talk", json={"topic": "test", "duration": 9999})
        finally:
            app_module.run_free_talk_thread = original

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["duration"], 1800)

    def test_talk_sessions_are_pruned_before_new_session(self):
        original_sessions = dict(app_module.talk_sessions)
        original_events = dict(app_module.talk_stop_events)
        app_module.talk_sessions.clear()
        app_module.talk_stop_events.clear()
        for index in range(app_module.MAX_TALK_SESSIONS):
            session_id = f"old-{index}"
            app_module.talk_sessions[session_id] = object()
            app_module.talk_stop_events[session_id] = object()
        try:
            app_module.prune_talk_sessions()

            self.assertEqual(len(app_module.talk_sessions), app_module.MAX_TALK_SESSIONS - 1)
            self.assertNotIn("old-0", app_module.talk_sessions)
        finally:
            app_module.talk_sessions.clear()
            app_module.talk_sessions.update(original_sessions)
            app_module.talk_stop_events.clear()
            app_module.talk_stop_events.update(original_events)

    def test_export_transcript_returns_markdown_attachment(self):
        app_module.conversation_history.extend([
            {"role": "user", "content": "@all summarize this"},
            {"role": "Mistral", "content": "Here is the summary."},
        ])

        with patch.object(
            app_module,
            "load_config",
            return_value={"room": {"title": "Demo Room"}},
        ):
            response = self.client.get("/export_transcript")

        body = response.data.decode("utf-8")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/markdown", response.content_type)
        self.assertIn(
            'attachment; filename="agent_meeting_room_transcript_',
            response.headers["Content-Disposition"],
        )
        self.assertIn("# Demo Room Transcript", body)
        self.assertIn("### 1. user", body)
        self.assertIn("@all summarize this", body)
        self.assertIn("### 2. Mistral", body)
        self.assertIn("Here is the summary.", body)

    def test_export_transcript_handles_empty_history(self):
        response = self.client.get("/export_transcript")

        body = response.data.decode("utf-8")
        self.assertEqual(response.status_code, 200)
        self.assertIn("_No messages yet._", body)

    def test_history_returns_current_conversation(self):
        app_module.conversation_history.extend([
            {"role": "user", "content": "Review this plan."},
            {"role": "Codex", "content": "The scope looks focused."},
        ])

        response = self.client.get("/history")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["messages"], app_module.conversation_history)

    def test_deliverable_types_returns_formats(self):
        response = self.client.get("/deliverable_types")

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            {"key": "code_review", "label": "Code Review Summary"},
            response.json["types"],
        )

    def test_generate_deliverable_returns_markdown(self):
        app_module.conversation_history.extend([
            {"role": "user", "content": "Ship structured meeting outputs."},
            {"role": "Codex", "content": "Add a deterministic Markdown generator."},
        ])

        with patch.object(
            app_module,
            "load_config",
            return_value={"room": {"title": "Delivery Room"}},
        ):
            response = self.client.post(
                "/generate_deliverable",
                json={"kind": "pull_request"},
            )

        self.assertEqual(response.status_code, 200)
        markdown = response.json["markdown"]
        self.assertIn("# Pull Request Description", markdown)
        self.assertIn("- Room: Delivery Room", markdown)
        self.assertIn("Ship structured meeting outputs.", markdown)

    def test_generate_deliverable_rejects_unknown_kind(self):
        response = self.client.post("/generate_deliverable", json={"kind": "bad"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["error"], "unknown deliverable type")

    def test_memory_search_rejects_empty_query(self):
        response = self.client.post("/memory_search", json={"query": "   "})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["error"], "empty query")

    def test_memory_search_returns_results(self):
        with patch.object(
            app_module,
            "search_memory",
            return_value=[{"title": "Note", "filename": "note.md", "snippet": "Useful note"}],
        ):
            response = self.client.post("/memory_search", json={"query": "useful"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["query"], "useful")
        self.assertEqual(response.json["results"][0]["title"], "Note")


if __name__ == "__main__":
    unittest.main()
