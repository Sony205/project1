import unittest, tempfile, os
from booklib.models import Book
from booklib.storage import Storage

class TestStorageJSON(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, "library.json")
        self.store = Storage(self.db)

    def tearDown(self):
        # освободим ссылки и удалим временную папку
        self.store = None
        try:
            self.tmp.cleanup()
        except PermissionError:
            import time, gc
            gc.collect()
            time.sleep(0.1)
            self.tmp.cleanup()

    def test_add_and_get(self):
        b = Book.create("Picnic", "AB Strugatsky", year=1972, genre="fantasy", tags=["classic"], pages=256)
        ok, dup = self.store.add(b)
        self.assertTrue(ok); self.assertIsNone(dup)
        out = self.store.get(b.id)
        self.assertIsNotNone(out)
        self.assertEqual(out.title, "Picnic")
        self.assertEqual(out.pages, 256)

    def test_duplicate_by_isbn(self):
        b1 = Book.create("T1", "A1", isbn="978-5-17-123456-7")
        b2 = Book.create("T2", "A2", isbn="978-5-17-123456-7")
        self.assertTrue(self.store.add(b1)[0])
        ok, dup = self.store.add(b2)
        self.assertFalse(ok); self.assertIsNotNone(dup)

    def test_duplicate_by_title_author_year(self):
        b1 = Book.create("Same", "Author", year=2000)
        b2 = Book.create("Same", "Author", year=2000)
        self.store.add(b1)
        ok, dup = self.store.add(b2)
        self.assertFalse(ok); self.assertIsNotNone(dup)

    def test_update_and_delete(self):
        b = Book.create("X", "Y")
        self.store.add(b)
        b.genre = "test"
        self.assertTrue(self.store.update(b))
        g = self.store.get(b.id)
        self.assertEqual(g.genre, "test")
        self.assertTrue(self.store.delete(b.id))
        self.assertIsNone(self.store.get(b.id))

if __name__ == "__main__":
    unittest.main()
