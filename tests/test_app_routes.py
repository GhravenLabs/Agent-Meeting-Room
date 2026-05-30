import unittest

import app as app_module


class AppRouteTests(unittest.TestCase):
    def setUp(self):
        self.client = app_module.app.test_client()
        app_module.conversation_history.clear()

    def test_chat_rejects_missing_message(self):
        response = self.client.post("/chat", json={})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["error"], "empty message")

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
