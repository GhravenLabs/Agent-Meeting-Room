import os
import tempfile
import unittest

import memory


class MemoryTests(unittest.TestCase):
    def test_safe_note_title_removes_reserved_filename_characters(self):
        title = memory.safe_note_title(' Review: A/B? "Notes" * ')

        self.assertEqual(title, "Review_A-B_Notes")

    def test_safe_note_title_falls_back_when_empty(self):
        self.assertEqual(memory.safe_note_title("   "), "Meeting_note")

    def test_local_memory_save_writes_note_and_rolling_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original_backend = memory.ACTIVE_BACKEND
            original_local_dir = memory.LOCAL_MEMORY_DIR
            memory.ACTIVE_BACKEND = "local"
            memory.LOCAL_MEMORY_DIR = tmpdir
            try:
                self.assertTrue(memory.save_to_obsidian("Review: A/B", "Useful note"))
                files = os.listdir(tmpdir)

                self.assertIn(memory.MEMORY_FILE, files)
                self.assertTrue(any(name.endswith("_Review_A-B.md") for name in files))
            finally:
                memory.ACTIVE_BACKEND = original_backend
                memory.LOCAL_MEMORY_DIR = original_local_dir


if __name__ == "__main__":
    unittest.main()
