
"""Модель данных для приложения книжной библиотеки.

Содержит dataclass `Book` с удобными фабриками `create()` и `from_dict()`.
Совместимо с JSON/SQLite стораджами и тестами.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Optional, Any, Dict
import uuid

def _now_iso() -> str:
    """Текущее время в ISO 8601 (UTC, сек.), с суффиксом 'Z'."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

def _to_int(val: Any) -> Optional[int]:
    if val is None or val == "":
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None

def _to_list_str(val: Any) -> List[str]:
    if val is None:
        return []
    if isinstance(val, list):
        return [str(x).strip() for x in val if str(x).strip()]
    # поддержка "a;b;c" и "a, b, c"
    s = str(val)
    if ";" in s:
        parts = s.split(";")
    elif "," in s:
        parts = s.split(",")
    else:
        parts = [s]
    return [p.strip() for p in parts if p.strip()]

@dataclass
class Book:
    """Книга в домашней библиотеке."""
    id: str
    title: str
    author: str
    year: Optional[int] = None
    genre: Optional[str] = None
    isbn: Optional[str] = None
    pages: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    quotes: List[str] = field(default_factory=list)
    added_at: str = field(default_factory=_now_iso)

    # --- Фабрики ---
    @staticmethod
    def create(title: str, author: str, *, year: Optional[int]=None,
               genre: Optional[str]=None, isbn: Optional[str]=None,
               pages: Optional[int]=None, tags: Optional[List[str]]=None,
               quotes: Optional[List[str]]=None, id: Optional[str]=None) -> "Book":
        return Book(
            id = id or str(uuid.uuid4()),
            title = str(title).strip(),
            author = str(author).strip(),
            year = _to_int(year),
            genre = (genre.strip() if isinstance(genre, str) and genre.strip() else None),
            isbn = (isbn.strip() if isinstance(isbn, str) and isbn.strip() else None),
            pages = _to_int(pages),
            tags = _to_list_str(tags),
            quotes = _to_list_str(quotes),
        )

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Book":
        # допускаем разные типы данных на входе; приводим
        return Book.create(
            id = d.get("id"),
            title = d.get("title") or "",
            author = d.get("author") or "",
            year = d.get("year"),
            genre = d.get("genre"),
            isbn = d.get("isbn"),
            pages = d.get("pages"),
            tags = d.get("tags"),
            quotes = d.get("quotes"),
        )

    # --- Сериализация ---
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # Нормализуем пустые строки к None для единообразия
        d["genre"] = self.genre if self.genre else None
        d["isbn"] = self.isbn if self.isbn else None
        return d
