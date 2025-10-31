from __future__ import annotations
import csv, json, os
from typing import List, Optional, Dict, Any, Tuple
from .models import Book

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
DEFAULT_PATH = os.path.join(PROJECT_ROOT, "library.json")

def _norm(s: Optional[str]) -> str:
    return (s or "").strip().casefold()

class Storage:
    def __init__(self, path: Optional[str] = None):
        env_path = os.environ.get("BOOKLIB_PATH", "").strip() or None
        self.path = path or env_path or DEFAULT_PATH
        d = os.path.dirname(self.path) or "."
        os.makedirs(d, exist_ok=True)
        if not os.path.exists(self.path):
            self._save_raw([])

    def _load_raw(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.path):
            return []
        with open(self.path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                return data if isinstance(data, list) else []
            except json.JSONDecodeError:
                return []

    def _save_raw(self, items: List[Dict[str, Any]]) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)

    def load(self) -> List[Book]:
        return [Book.from_dict(x) for x in self._load_raw()]

    def save(self, books: List[Book]) -> None:
        self._save_raw([b.to_dict() for b in books])

    def _find_duplicate(self, books: List[Book], cand: Book) -> Optional[Book]:
        for b in books:
            if _norm(b.isbn) and _norm(cand.isbn) and _norm(b.isbn) == _norm(cand.isbn):
                return b
            if _norm(b.title) == _norm(cand.title) and _norm(b.author) == _norm(cand.author):
                if (b.year is None and cand.year is None) or (b.year == cand.year):
                    return b
        return None

    def add(self, book: Book) -> Tuple[bool, Optional[Book]]:
        books = self.load()
        dup = self._find_duplicate(books, book)
        if dup:
            return False, dup
        books.append(book)
        self.save(books)
        return True, None

    def get(self, book_id: str) -> Optional[Book]:
        for b in self.load():
            if b.id == book_id:
                return b
        return None

    def update(self, book: Book) -> bool:
        books = self.load()
        for i, b in enumerate(books):
            if b.id == book.id:
                books[i] = book
                self.save(books)
                return True
        return False

    def delete(self, book_id: str) -> bool:
        books = self.load()
        new_books = [b for b in books if b.id != book_id]
        if len(new_books) != len(books):
            self.save(new_books)
            return True
        return False

    CSV_FIELDS = ["id","title","author","year","genre","tags","isbn","pages","quotes","added_at"]

    def export_csv(self, csv_path: str) -> int:
        books = self.load()
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=self.CSV_FIELDS)
            w.writeheader()
            for b in books:
                d = b.to_dict()
                d["tags"] = ";".join(d.get("tags", []))
                d["quotes"] = "|".join(d.get("quotes", []))
                w.writerow(d)
        return len(books)

    def import_csv(self, csv_path: str) -> int:
        count = 0
        books: List[Book] = self.load()
        seen_ids = {b.id for b in books}
        with open(csv_path, "r", encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                row["year"]  = int(row["year"])  if row.get("year")  else None
                row["pages"] = int(row["pages"]) if row.get("pages") else None
                row["tags"]  = [t for t in (row.get("tags","" ).split(";")) if t]
                row["quotes"]= [q for q in (row.get("quotes","" ).split("|")) if q]
                book = Book.from_dict(row)
                if book.id in seen_ids:
                    books = [b for b in books if b.id != book.id]
                    books.append(book)
                    count += 1
                    continue
                dup = self._find_duplicate(books, book)
                if dup:
                    continue
                books.append(book)
                seen_ids.add(book.id)
                count += 1
        self.save(books)
        return count
