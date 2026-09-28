import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import memory


class MemoryBudgetTests(unittest.TestCase):
    def test_nonpositive_budget_returns_no_context(self):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, memory.MEMORY_FILE).write_text("saved meeting context", encoding="utf-8")
            with patch.object(memory, "ACTIVE_BACKEND", "local"), \
                    patch.object(memory, "LOCAL_MEMORY_DIR", folder):
                for budget in (0, -1, -100):
                    with self.subTest(budget=budget):
                        self.assertEqual(memory.get_recent_memory(budget), "")

    def test_positive_budget_keeps_recent_context(self):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, memory.MEMORY_FILE).write_text("old context, recent", encoding="utf-8")
            with patch.object(memory, "ACTIVE_BACKEND", "local"), \
                    patch.object(memory, "LOCAL_MEMORY_DIR", folder):
                self.assertEqual(memory.get_recent_memory(6), "...recent")
                self.assertEqual(memory.get_recent_memory(100), "old context, recent")
