import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

from clara_core import storage

class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "test.sqlite3"
        self.db_patch = patch.object(storage, "DB_PATH", self.db)
        self.dir_patch = patch.object(storage, "DATA_DIR", Path(self.temp.name))
        self.db_patch.start(); self.dir_patch.start()
        storage.init_db()

    def tearDown(self):
        self.dir_patch.stop(); self.db_patch.stop(); self.temp.cleanup()

    def test_create_add_list_and_delete(self):
        conversation = storage.create_conversation("Test")
        self.assertEqual(conversation["title"], "Test")
        msg = storage.add_message(conversation["id"], "user", "Ciao")
        self.assertEqual(msg["content"], "Ciao")
        self.assertEqual(len(storage.get_messages(conversation["id"])), 1)
        self.assertEqual(storage.list_conversations()[0]["message_count"], 1)
        self.assertTrue(storage.delete_conversation(conversation["id"]))
        self.assertEqual(storage.database_stats()["messages"], 0)

    def test_truncate_and_feedback(self):
        conversation = storage.create_conversation("T")
        storage.add_message(conversation["id"], "user", "a")
        reply = storage.add_message(conversation["id"], "assistant", "b")
        storage.add_message(conversation["id"], "user", "c")
        self.assertTrue(storage.set_feedback(reply["id"], "up"))
        self.assertEqual(storage.get_messages(conversation["id"])[1]["feedback"], "up")
        self.assertEqual(storage.truncate_messages(conversation["id"], 1), 2)
        self.assertEqual(len(storage.get_messages(conversation["id"])), 1)
        with self.assertRaises(ValueError):
            storage.set_feedback(1, "boh")

    def test_plan_limits_and_three_hour_window(self):
        snapshot = storage.usage_snapshot()
        self.assertEqual(snapshot["plan"], "free")
        self.assertEqual(snapshot["token_limit"], 300_000)
        self.assertEqual(snapshot["window_seconds"], 3 * 60 * 60)
        self.assertEqual(storage.set_usage_plan("pro")["token_limit"], 1_000_000)
        self.assertEqual(storage.set_usage_plan("max")["token_limit"], 3_000_000)
        self.assertEqual(storage.set_usage_plan("free")["plan"], "free")
        with self.assertRaises(ValueError):
            storage.set_usage_plan("enterprise")

    def test_rename(self):
        conversation = storage.create_conversation()
        self.assertTrue(storage.rename_conversation(conversation["id"], "Titolo aggiornato"))
        self.assertEqual(storage.get_conversation(conversation["id"])["title"], "Titolo aggiornato")

if __name__ == "__main__":
    unittest.main()

