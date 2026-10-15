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

    def test_safe_markdown_heading_collapses_markup_and_newlines(self):
        title = "Review\n# Injected <script> & notes"

        self.assertEqual(
            memory.safe_markdown_heading(title),
            "Review Injected &lt;script&gt; &amp; notes",
        )

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

    def test_local_memory_save_uses_safe_title_in_markdown_headings(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original_backend = memory.ACTIVE_BACKEND
            original_local_dir = memory.LOCAL_MEMORY_DIR
            memory.ACTIVE_BACKEND = "local"
            memory.LOCAL_MEMORY_DIR = tmpdir
            try:
                self.assertTrue(memory.save_to_obsidian("Review\n# Injected <script>", "Useful note"))
                note_paths = [
                    os.path.join(tmpdir, name)
                    for name in os.listdir(tmpdir)
                    if name != memory.MEMORY_FILE
                ]
                with open(note_paths[0], encoding="utf-8") as note_file:
                    note = note_file.read()
                with open(os.path.join(tmpdir, memory.MEMORY_FILE), encoding="utf-8") as rolling_file:
                    rolling = rolling_file.read()
                self.assertTrue(note.startswith("# Review Injected &lt;script&gt;\n"))
                self.assertIn("## Review Injected &lt;script&gt; —", rolling)
                self.assertNotIn("\n# Injected", note)
                self.assertNotIn("\n# Injected", rolling)
            finally:
                memory.ACTIVE_BACKEND = original_backend
                memory.LOCAL_MEMORY_DIR = original_local_dir

    def test_search_memory_returns_matching_notes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original_backend = memory.ACTIVE_BACKEND
            original_local_dir = memory.LOCAL_MEMORY_DIR
            memory.ACTIVE_BACKEND = "local"
            memory.LOCAL_MEMORY_DIR = tmpdir
            try:
                path = os.path.join(tmpdir, "20260608_Code_Review.md")
                with open(path, "w", encoding="utf-8") as f:
                    f.write("# Code Review\n\nDiscussed transcript export and memory search.")

                results = memory.search_memory("memory search")

                self.assertEqual(len(results), 1)
                self.assertEqual(results[0]["title"], "Code Review")
                self.assertEqual(results[0]["filename"], "20260608_Code_Review.md")
                self.assertIn("memory search", results[0]["snippet"])
            finally:
                memory.ACTIVE_BACKEND = original_backend
                memory.LOCAL_MEMORY_DIR = original_local_dir

    def test_search_memory_ignores_empty_query(self):
        self.assertEqual(memory.search_memory("   "), [])


if __name__ == "__main__":
    unittest.main()
