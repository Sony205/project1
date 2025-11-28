"""SQLite‑хранилище для `booklib` с явными COMMIT и закрытием соединений."""
from __future__ import annotations
import os, sqlite3
from typing import List, Optional, Tuple
from contextlib import contextmanager
from .models import Book

def _norm(s: Optional[str]) -> str:
    return (s or "").strip().casefold()

class SqliteStorage:
    """Хранилище на SQLite; интерфейс совместим с JSON‑Storage."""
    def __init__(self, path: str):
        self.path = path
        d = os.path.dirname(self.path) or "."
        os.makedirs(d, exist_ok=True)
        self._init_db()

    @contextmanager
    def _db(self):
        con = sqlite3.connect(self.path)
        try:
            con.row_factory = sqlite3.Row
            con.execute("PRAGMA foreign_keys = ON;")
            yield con
        finally:
            con.close()

    def _init_db(self):
        with self._db() as con:
            con.executescript(
                """
                CREATE TABLE IF NOT EXISTS books(
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    author TEXT NOT NULL,
                    year INTEGER NULL,
                    genre TEXT NULL,
                    isbn TEXT NULL,
                    pages INTEGER NULL,
                    added_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tags(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id TEXT NOT NULL,
                    tag TEXT NOT NULL,
                    FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS quotes(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id TEXT NOT NULL,
                    text TEXT NOT NULL,
                    FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_books_title ON books(title);
                CREATE INDEX IF NOT EXISTS idx_books_author ON books(author);
                CREATE INDEX IF NOT EXISTS idx_books_year ON books(year);
                CREATE INDEX IF NOT EXISTS idx_tags_book ON tags(book_id);
                CREATE INDEX IF NOT EXISTS idx_quotes_book ON quotes(book_id);
                """
            )
            con.commit()

    def _row_to_book(self, con, row: sqlite3.Row) -> Book:
        tags = [r["tag"] for r in con.execute("SELECT tag FROM tags WHERE book_id=?;", (row["id"],))]
        quotes = [r["text"] for r in con.execute("SELECT text FROM quotes WHERE book_id=? ORDER BY id;", (row["id"],))]
        return Book(
            id=row["id"], title=row["title"], author=row["author"],
            year=row["year"], genre=row["genre"], isbn=row["isbn"], pages=row["pages"],
            tags=tags, quotes=quotes, added_at=row["added_at"]
        )

    def load(self) -> List[Book]:
        with self._db() as con:
            cur = con.execute("SELECT * FROM books ORDER BY title, author;")
            return [self._row_to_book(con, r) for r in cur.fetchall()]

    def save(self, books: List[Book]) -> None:
        with self._db() as con:
            con.execute("DELETE FROM quotes;")
            con.execute("DELETE FROM tags;")
            con.execute("DELETE FROM books;")
            for b in books:
                con.execute(
                    "INSERT INTO books(id,title,author,year,genre,isbn,pages,added_at) VALUES(?,?,?,?,?,?,?,?);",
                    (b.id, b.title, b.author, b.year, b.genre, b.isbn, b.pages, b.added_at),
                )
                for t in (b.tags or []):
                    if t.strip():
                        con.execute("INSERT INTO tags(book_id, tag) VALUES(?,?);", (b.id, t))
                for q in (b.quotes or []):
                    if q.strip():
                        con.execute("INSERT INTO quotes(book_id, text) VALUES(?,?);", (b.id, q))
            con.commit()

    def _find_duplicate(self, con, cand: Book):
        if cand.isbn:
            row = con.execute("SELECT * FROM books WHERE isbn IS NOT NULL AND LOWER(isbn)=LOWER(?);", (cand.isbn,)).fetchone()
            if row: return self._row_to_book(con, row)
        rows = con.execute("SELECT * FROM books WHERE LOWER(title)=LOWER(?) AND LOWER(author)=LOWER(?);",
                           (cand.title, cand.author)).fetchall()
        for r in rows:
            if (r["year"] is None and cand.year is None) or (r["year"] == cand.year):
                return self._row_to_book(con, r)
        return None

    def add(self, book: Book) -> Tuple[bool, Optional[Book]]:
        with self._db() as con:
            dup = self._find_duplicate(con, book)
            if dup: return False, dup
            con.execute(
                "INSERT INTO books(id,title,author,year,genre,isbn,pages,added_at) VALUES(?,?,?,?,?,?,?,?);",
                (book.id, book.title, book.author, book.year, book.genre, book.isbn, book.pages, book.added_at),
            )
            for t in (book.tags or []):
                if t.strip():
                    con.execute("INSERT INTO tags(book_id, tag) VALUES(?,?);", (book.id, t))
            for q in (book.quotes or []):
                if q.strip():
                    con.execute("INSERT INTO quotes(book_id, text) VALUES(?,?);", (book.id, q))
            con.commit()
            return True, None

    def get(self, book_id: str) -> Optional[Book]:
        with self._db() as con:
            row = con.execute("SELECT * FROM books WHERE id=?;", (book_id,)).fetchone()
            return self._row_to_book(con, row) if row else None

    def update(self, book: Book) -> bool:
        with self._db() as con:
            if not con.execute("SELECT 1 FROM books WHERE id=?;", (book.id,)).fetchone():
                return False
            con.execute(
                "UPDATE books SET title=?, author=?, year=?, genre=?, isbn=?, pages=?, added_at=? WHERE id=?;",
                (book.title, book.author, book.year, book.genre, book.isbn, book.pages, book.added_at, book.id),
            )
            con.execute("DELETE FROM tags WHERE book_id=?;", (book.id,))
            for t in (book.tags or []):
                if t.strip():
                    con.execute("INSERT INTO tags(book_id, tag) VALUES(?,?);", (book.id, t))
            con.execute("DELETE FROM quotes WHERE book_id=?;", (book.id,))
            for q in (book.quotes or []):
                if q.strip():
                    con.execute("INSERT INTO quotes(book_id, text) VALUES(?,?);", (book.id, q))
            con.commit()
            return True

    def delete(self, book_id: str) -> bool:
        with self._db() as con:
            cur = con.execute("DELETE FROM books WHERE id=?;", (book_id,))
            con.commit()
            return cur.rowcount > 0

    CSV_FIELDS = ["id","title","author","year","genre","tags","isbn","pages","quotes","added_at"]

    def export_csv(self, csv_path: str) -> int:
        import csv
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
        import csv
        count = 0
        with self._db() as con, open(csv_path, "r", encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                year  = int(row["year"])  if row.get("year")  else None
                pages = int(row["pages"]) if row.get("pages") else None
                tags  = [t for t in (row.get("tags","").split(";")) if t]
                quotes= [q for q in (row.get("quotes","").split("|")) if q]
                b = Book.from_dict({
                    "id": row.get("id"),
                    "title": row["title"],
                    "author": row["author"],
                    "year": year,
                    "genre": row.get("genre"),
                    "isbn": row.get("isbn"),
                    "pages": pages,
                    "tags": tags,
                    "quotes": quotes,
                    "added_at": row.get("added_at"),
                })
                if con.execute("SELECT 1 FROM books WHERE id=?;", (b.id,)).fetchone():
                    con.execute(
                        "UPDATE books SET title=?, author=?, year=?, genre=?, isbn=?, pages=?, added_at=? WHERE id=?;",
                        (b.title, b.author, b.year, b.genre, b.isbn, b.pages, b.added_at, b.id),
                    )
                    con.execute("DELETE FROM tags WHERE book_id=?;", (b.id,))
                    for t in (b.tags or []):
                        con.execute("INSERT INTO tags(book_id, tag) VALUES(?,?);", (b.id, t))
                    con.execute("DELETE FROM quotes WHERE book_id=?;", (b.id,))
                    for q in (b.quotes or []):
                        con.execute("INSERT INTO quotes(book_id, text) VALUES(?,?);", (b.id, q))
                    count += 1
                    continue
                dup = self._find_duplicate(con, b)
                if dup:
                    continue
                con.execute(
                    "INSERT INTO books(id,title,author,year,genre,isbn,pages,added_at) VALUES(?,?,?,?,?,?,?,?);",
                    (b.id, b.title, b.author, b.year, b.genre, b.isbn, b.pages, b.added_at),
                )
                for t in (b.tags or []):
                    con.execute("INSERT INTO tags(book_id, tag) VALUES(?,?);", (b.id, t))
                for q in (b.quotes or []):
                    con.execute("INSERT INTO quotes(book_id, text) VALUES(?,?);", (b.id, q))
                count += 1
            con.commit()
        return count
