import unittest, tempfile, os, io
from contextlib import redirect_stdout
from booklib.models import Book
from booklib.storage import Storage
from booklib import commands as C

class TestCommandsQuotes(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, "library.json")
        self.store = Storage(self.db)
        b = Book.create("T","A")
        self.store.add(b)
        self.bid = b.id

    def tearDown(self):
        self.store = None
        try:
            self.tmp.cleanup()
        except PermissionError:
            import time, gc
            gc.collect(); time.sleep(0.1)
            self.tmp.cleanup()

    class Args:
        pass

    def test_add_duplicate_quote(self):
        args = self.Args()
        args.id = self.bid
        args.text = "  Quote  "
        f = io.StringIO()
        with redirect_stdout(f):
            C.cmd_add_quote(args, self.store)   # first time => added
            C.cmd_add_quote(args, self.store)   # second time => duplicate
        out = f.getvalue()
        self.assertIn("Цитата добавлена.", out)
        self.assertIn("Пропущено: такая цитата уже есть.", out)

if __name__ == "__main__":
    unittest.main()
