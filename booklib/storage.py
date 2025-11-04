"""Файловое хранилище библиотеки (JSON + CSV).

По умолчанию база данных хранится в файле ``library.json`` рядом с ``main.py``
(то есть в корне проекта). Путь можно переопределить опцией ``--db``.
"""
from __future__ import annotations
import csv, json, os
from typing import List, Optional, Dict, Any, Tuple
from .models import Book

# --- По умолчанию хранение рядом с main.py (корень проекта) ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
DEFAULT_PATH = os.path.join(PROJECT_ROOT, "library.json")

def _norm(s: Optional[str]) -> str:
    """Приводит строку к нормальной форме для сравнения (lower+trim).

    Args:
        s: Входная строка.
    Returns:
        str: Нормализованная строка.
    """
    return (s or "").strip().casefold()

class Storage:
    """JSON‑хранилище книжной библиотеки.

    Приоритет путей:
        1) явный ``path`` (из ``--db``);
        2) иначе ``DEFAULT_PATH`` (``./library.json`` рядом с ``main.py``).

    Обнаружение дубликатов выполняется по ``ISBN`` или по тройке
    (``title`` + ``author`` + ``year``).
    """
    def __init__(self, path: Optional[str] = None):
        """Инициализирует хранилище.

        Args:
            path: Необязательный путь к JSON-файлу базы.
        """
        self.path = path or DEFAULT_PATH
        d = os.path.dirname(self.path) or "."
        os.makedirs(d, exist_ok=True)
        if not os.path.exists(self.path):
            self._save_raw([])

    # --- низкоуровневые операции ---
    def _load_raw(self) -> List[Dict[str, Any]]:
        """Читает «сырой» JSON-список книг из файла.

        Returns:
            list[dict]: Список словарей книг. При ошибке парсинга — пустой список.
        """
        if not os.path.exists(self.path):
            return []
        with open(self.path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                return data if isinstance(data, list) else []
            except json.JSONDecodeError:
                return []

    def _save_raw(self, items: List[Dict[str, Any]]) -> None:
        """Записывает «сырой» список словарей в JSON-файл.

        Args:
            items: Сериализуемые записи книг.
        """
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)

    # --- модельные операции ---
    def load(self) -> List[Book]:
        """Загружает все книги в объекты :class:`Book`.

        Returns:
            list[Book]: Список книг.
        """
        return [Book.from_dict(x) for x in self._load_raw()]

    def save(self, books: List[Book]) -> None:
        """Сохраняет список книг в файл.

        Args:
            books: Записи для сохранения.
        """
        self._save_raw([b.to_dict() for b in books])

    # --- дубликаты ---
    def _find_duplicate(self, books: List[Book], cand: Book) -> Optional[Book]:
        """Ищет дубликат книги среди уже сохранённых.

        Args:
            books: Существующие книги.
            cand: Кандидат на добавление.

        Returns:
            Optional[Book]: Найденный дубликат или ``None``.
        """
        for b in books:
            if _norm(b.isbn) and _norm(cand.isbn) and _norm(b.isbn) == _norm(cand.isbn):
                return b
            if _norm(b.title) == _norm(cand.title) and _norm(b.author) == _norm(cand.author):
                if (b.year is None and cand.year is None) or (b.year == cand.year):
                    return b
        return None

    def add(self, book: Book) -> Tuple[bool, Optional[Book]]:
        """Добавляет книгу в хранилище.

        Args:
            book: Экземпляр :class:`Book`.

        Returns:
            Tuple[bool, Optional[Book]]: ``(True, None)`` при успехе;             ``(False, existing)`` если найден дубликат.
        """
        books = self.load()
        dup = self._find_duplicate(books, book)
        if dup:
            return False, dup
        books.append(book)
        self.save(books)
        return True, None

    def get(self, book_id: str) -> Optional[Book]:
        """Возвращает книгу по UUID.

        Args:
            book_id: Идентификатор книги.

        Returns:
            Optional[Book]: Книга или ``None``.
        """
        for b in self.load():
            if b.id == book_id:
                return b
        return None

    def update(self, book: Book) -> bool:
        """Обновляет существующую запись книги.

        Args:
            book: Книга с обновлёнными полями.

        Returns:
            bool: ``True`` — если запись найдена и обновлена.
        """
        books = self.load()
        for i, b in enumerate(books):
            if b.id == book.id:
                books[i] = book
                self.save(books)
                return True
        return False

    def delete(self, book_id: str) -> bool:
        """Удаляет книгу по UUID.

        Args:
            book_id: Идентификатор книги.

        Returns:
            bool: ``True`` — если запись была удалена.
        """
        books = self.load()
        new_books = [b for b in books if b.id != book_id]
        if len(new_books) != len(books):
            self.save(new_books)
            return True
        return False

    # --- CSV импорт/экспорт ---
    CSV_FIELDS = ["id","title","author","year","genre","tags","isbn","pages","quotes","added_at"]

    def export_csv(self, csv_path: str) -> int:
        """Экспортирует базу в CSV.

        Args:
            csv_path: Путь к целевому CSV-файлу.

        Returns:
            int: Количество экспортированных записей.
        """
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
        """Импортирует записи из CSV.

        Поведение:
          * если ``id`` совпал — запись обновляется;
          * если дубликат по полям — пропускается;
          * иначе — добавляется как новая.

        Args:
            csv_path: Путь к исходному CSV.

        Returns:
            int: Количество добавленных/обновлённых записей.
        """
        count = 0
        books: List[Book] = self.load()
        seen_ids = {b.id for b in books}
        with open(csv_path, "r", encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                row["year"]  = int(row["year"])  if row.get("year")  else None
                row["pages"] = int(row["pages"]) if row.get("pages") else None
                row["tags"]  = [t for t in (row.get("tags","").split(";")) if t]
                row["quotes"]= [q for q in (row.get("quotes","").split("|")) if q]
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
