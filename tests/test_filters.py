import unittest
from booklib.models import Book
from booklib.filters import search, sort_books

class TestFilters(unittest.TestCase):
    def setUp(self):
        self.books = [
            Book.create("B", "A", year=2000, genre="x", tags=["t1"]),
            Book.create("A", "B", year=1990, genre="y", tags=["t2"]),
            Book.create("C", "A", year=2010, genre="x", tags=["t1","t3"]),
        ]

    def test_search_by_author(self):
        res = search(self.books, author="A", exact=True)
        self.assertEqual(len(res), 2)

    def test_search_by_tag(self):
        res = search(self.books, tag="t3")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].title, "C")

    def test_sort(self):
        res = sort_books(self.books, by="title")
        self.assertEqual([b.title for b in res], ["A","B","C"])

if __name__ == "__main__":
    unittest.main()
