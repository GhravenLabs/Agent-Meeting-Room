import os
import tempfile
import unittest
from unittest.mock import patch

import memory


class MemoryEncodingTests(unittest.TestCase):
    def test_search_skips_invalid_utf8_and_keeps_valid_matches(self):
        with tempfile.TemporaryDirectory() as folder:
            with open(os.path.join(folder, "z_broken.md"), "wb") as note:
                note.write(b"# Broken\nmeeting \xff")
            with open(os.path.join(folder, "a_valid.md"), "w", encoding="utf-8") as note:
                note.write("# Review\nUseful meeting notes")
            with (
                patch.object(memory, "ACTIVE_BACKEND", "local"),
                patch.object(memory, "LOCAL_MEMORY_DIR", folder),
            ):
                results = memory.search_memory("meeting")
                self.assertEqual([item["filename"] for item in results], ["a_valid.md"])
                self.assertIn("meeting", results[0]["snippet"])
                self.assertEqual(memory.search_memory("absent"), [])


if __name__ == "__main__":
    unittest.main()
