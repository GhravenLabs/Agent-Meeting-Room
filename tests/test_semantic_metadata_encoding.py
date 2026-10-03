import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import semantic_memory


class SemanticMetadataEncodingTests(unittest.TestCase):
    def test_invalid_utf8_reports_unavailable_without_rewriting_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(semantic_memory._meta_path(folder))
            path.parent.mkdir()
            original = b'[{"title": "broken\xff"}]'
            path.write_bytes(original)
            with (
                patch.dict(os.environ, {"SEMANTIC_MEMORY_ENABLED": "true"}),
                patch.object(semantic_memory, "_optional_vector_modules", return_value=(object(), object(), "")),
                patch.object(semantic_memory, "embed_text") as embed,
            ):
                for operation in (
                    lambda: semantic_memory.semantic_status(folder),
                    lambda: semantic_memory.search_semantic_memory(folder, "meeting"),
                ):
                    with self.subTest(operation=operation):
                        result = operation()
                        self.assertFalse(result["available"])
                        self.assertIn("metadata", result["error"])
                embed.assert_not_called()
            self.assertEqual(path.read_bytes(), original)
