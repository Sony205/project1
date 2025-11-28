import unittest
from booklib.models import Book

class TestModels(unittest.TestCase):
    def test_book_create_uuid(self):
        b1 = Book.create(title="A", author="B")
        b2 = Book.create(title="A2", author="B2")
        self.assertNotEqual(b1.id, b2.id)
        self.assertEqual(len(b1.id), 36)
        self.assertTrue(b1.added_at.endswith("Z"))

    def test_from_dict_coercion(self):
        data = {"title":"T","author":"A","year":"1999","pages":"123"}
        b = Book.from_dict(data)
        self.assertEqual(b.year, 1999)
        self.assertEqual(b.pages, 123)

if __name__ == "__main__":
    unittest.main()
