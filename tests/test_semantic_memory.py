import os
import tempfile
import unittest
from unittest.mock import patch

import semantic_memory


class SemanticMemoryTests(unittest.TestCase):
    def test_search_semantic_memory_reports_disabled(self):
        with patch.dict(os.environ, {"SEMANTIC_MEMORY_ENABLED": "false"}):
            result = semantic_memory.search_semantic_memory("notes", "desktop packaging")

        self.assertFalse(result["available"])
        self.assertEqual(result["results"], [])
        self.assertEqual(result["error"], "semantic memory disabled")

    def test_semantic_status_includes_index_count(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, semantic_memory.SEMANTIC_DIR_NAME))
            semantic_memory._save_metadata(
                tmpdir,
                [{"title": "One"}, {"title": "Two"}],
            )

            with patch.dict(os.environ, {"SEMANTIC_MEMORY_ENABLED": "false"}):
                status = semantic_memory.semantic_status(tmpdir)

        self.assertFalse(status["enabled"])
        self.assertEqual(status["indexed_notes"], 2)

    def test_embed_text_falls_back_to_legacy_ollama_endpoint(self):
        class FakeResponse:
            def __init__(self, payload, raises=False):
                self.payload = payload
                self.raises = raises

            def raise_for_status(self):
                if self.raises:
                    raise semantic_memory.requests.RequestException("failed")

            def json(self):
                return self.payload

        calls = []

        def fake_post(url, json, timeout):
            calls.append(url)
            if url.endswith("/api/embed"):
                return FakeResponse({}, raises=True)
            return FakeResponse({"embedding": [0.1, 0.2, 0.3]})

        embedding = semantic_memory.embed_text("hello", post=fake_post)

        self.assertEqual(embedding, [0.1, 0.2, 0.3])
        self.assertTrue(calls[0].endswith("/api/embed"))
        self.assertTrue(calls[1].endswith("/api/embeddings"))


if __name__ == "__main__":
    unittest.main()
