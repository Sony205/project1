import unittest, tempfile, os, time, gc
from booklib.models import Book
from booklib.storage_sqlite import SqliteStorage

class TestStorageSQLite(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, "library.db")
        self.store = SqliteStorage(self.db)

    def tearDown(self):
        self.store = None
        gc.collect()
        for _ in range(5):
            try:
                self.tmp.cleanup()
                break
            except PermissionError:
                time.sleep(0.1)

    def test_add_get_tags_quotes(self):
        b = Book.create("Dune", "F. Herbert", year=1965, genre="sf", tags=["epic","space"], pages=688)
        self.assertTrue(self.store.add(b)[0])
        got = self.store.get(b.id)
        self.assertIsNotNone(got)
        self.assertEqual(got.title, "Dune")
        got.quotes.append("Fear is the mind-killer.")
        self.store.update(got)
        again = self.store.get(b.id)
        self.assertIn("Fear is the mind-killer.", again.quotes)

    def test_duplicates(self):
        b1 = Book.create("Same", "Auth", year=2000)
        b2 = Book.create("Same", "Auth", year=2000)
        self.assertTrue(self.store.add(b1)[0])
        ok, dup = self.store.add(b2)
        self.assertFalse(ok); self.assertIsNotNone(dup)

if __name__ == "__main__":
    unittest.main()
