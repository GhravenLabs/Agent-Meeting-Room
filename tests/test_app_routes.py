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


if __name__ == "__main__":
    unittest.main()
