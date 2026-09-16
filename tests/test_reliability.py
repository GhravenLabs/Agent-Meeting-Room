import tempfile
import threading
import queue
import unittest
from pathlib import Path
from unittest.mock import patch

import app
import customization
import memory


class ReliabilityTests(unittest.TestCase):
    def test_invalid_payloads_return_client_errors(self):
        client = app.app.test_client()
        routes = {
            "/chat": "message", "/save_memory": "content",
            "/project_context": "path", "/generate_deliverable": "kind",
            "/memory_search": "query", "/semantic_memory_search": "query",
            "/talk": "topic",
        }
        for route, field in routes.items():
            for payload in ([1], "text", 1, {field: None}, {field: []}):
                with self.subTest(route=route, payload=payload):
                    response = client.post(route, json=payload)
                    self.assertEqual(response.status_code, 400)
                    self.assertIn("error", response.json)
        self.assertEqual(client.post("/customization", json=[1]).status_code, 400)

    def test_disconnected_stream_stops_worker(self):
        event = threading.Event()
        messages = queue.Queue()
        messages.put({"agent": "Test", "message": "hello"})
        with (
            patch.dict(app.talk_sessions, {"test-disconnect": messages}, clear=True),
            patch.dict(app.talk_stop_events, {"test-disconnect": event}, clear=True),
            patch.object(app, "conversation_history", []),
        ):
            response = app.app.test_client().get("/talk_stream/test-disconnect", buffered=False)
            response.close()
            self.assertTrue(event.is_set())
            self.assertNotIn("test-disconnect", app.talk_sessions)

    def test_zero_duration_uses_minimum_not_room_default(self):
        with (
            patch.object(app.threading, "Thread"),
            patch.object(app, "build_agent_context", return_value=""),
            patch.object(app, "get_room_config", return_value={"free_talk_duration": 900}),
            patch.dict(app.talk_sessions, {}, clear=True),
            patch.dict(app.talk_stop_events, {}, clear=True),
            patch.object(app, "conversation_history", []),
        ):
            response = app.app.test_client().post("/talk", json={"topic": "test", "duration": 0})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json["duration"], 60)

    def test_malformed_config_values_use_safe_defaults(self):
        config = customization.normalize_config({
            "room": {"theme": [], "free_talk_duration": float("inf"),
                     "response_word_limit": float("-inf")},
            "presets": {"mixed": {"agents": [[], {}, "mistral"]}},
        })
        self.assertEqual(config["room"]["theme"], "dark")
        self.assertEqual(config["room"]["free_talk_duration"], 300)
        self.assertEqual(config["room"]["response_word_limit"], 150)
        self.assertEqual(config["presets"]["mixed"]["agents"], ["mistral"])

    def test_repeated_note_titles_preserve_both_contents(self):
        with (
            tempfile.TemporaryDirectory() as folder,
            patch.object(memory, "ACTIVE_BACKEND", "local"),
            patch.object(memory, "LOCAL_MEMORY_DIR", folder),
            patch.object(memory, "index_note"),
            patch.object(memory, "datetime") as clock,
        ):
            clock.now.return_value.strftime.return_value = "20260916_1900"
            self.assertTrue(memory.save_to_obsidian("Review", "first content"))
            self.assertTrue(memory.save_to_obsidian("Review", "second content"))
            notes = list(Path(folder).glob("*_Review.md"))
            self.assertEqual(len(notes), 2)
            contents = [note.read_text(encoding="utf-8") for note in notes]
            self.assertTrue(any("first content" in text for text in contents))
            self.assertTrue(any("second content" in text for text in contents))
