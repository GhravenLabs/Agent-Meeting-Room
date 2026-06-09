import os
import tempfile
import unittest

from project_context import summarize_project


class ProjectContextTests(unittest.TestCase):
    def test_summarize_project_indexes_useful_files_and_skips_dependencies(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "README.md"), "w", encoding="utf-8") as handle:
                handle.write("# Demo\n\nA tiny project.")
            with open(os.path.join(tmpdir, "app.py"), "w", encoding="utf-8") as handle:
                handle.write("def hello():\n    return 'world'\n")
            os.makedirs(os.path.join(tmpdir, "node_modules"))
            with open(os.path.join(tmpdir, "node_modules", "ignored.js"), "w", encoding="utf-8") as handle:
                handle.write("console.log('ignore me')")

            summary = summarize_project(tmpdir)

        paths = [item["path"] for item in summary["files"]]
        self.assertIn("README.md", paths)
        self.assertIn("app.py", paths)
        self.assertNotIn("node_modules/ignored.js", paths)
        self.assertIn("PROJECT CONTEXT LOADED", summary["context"])
        self.assertIn("A tiny project.", summary["context"])

    def test_summarize_project_rejects_missing_folder(self):
        with self.assertRaises(ValueError):
            summarize_project(os.path.join(tempfile.gettempdir(), "missing-agent-room-project"))


if __name__ == "__main__":
    unittest.main()
