"""Модели данных для библиотеки.

Содержит dataclass :class:`~booklib.models.Book` — основную сущность каталога,
а также служебные функции для генерации метаданных.
Докстринги оформлены в стиле Google (поддерживаются Sphinx Napoleon).
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

def _now_iso() -> str:
    """Возвращает текущий момент времени в ISO 8601 (UTC, сек. точности).

    Returns:
        str: Строка ISO вида ``YYYY-MM-DDTHH:MM:SSZ``.
    """
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

@dataclass
class Book:
    """Книга в домашней библиотеке.

    Атрибуты:
        id (str): UUID книги в текстовом виде.
        title (str): Название книги.
        author (str): Автор(ы) книги.
        year (Optional[int]): Год издания (если известен).
        genre (Optional[str]): Жанр.
        tags (List[str]): Список тегов.
        isbn (Optional[str]): ISBN (если есть).
        pages (Optional[int]): Количество страниц.
        quotes (List[str]): Цитаты, привязанные к книге.
        added_at (str): Момент добавления в ISO 8601.
    """
    id: str
    title: str
    author: str
    year: Optional[int] = None
    genre: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    isbn: Optional[str] = None
    pages: Optional[int] = None
    quotes: List[str] = field(default_factory=list)
    added_at: str = field(default_factory=_now_iso)

    @staticmethod
    def create(
        title: str,
        author: str,
        year: Optional[int] = None,
        genre: Optional[str] = None,
        tags: Optional[List[str]] = None,
        isbn: Optional[str] = None,
        pages: Optional[int] = None,
    ) -> "Book":
        """Фабричный метод создания новой книги с генерируемым UUID.

        Args:
            title: Название книги.
            author: Автор(ы) книги.
            year: Год издания.
            genre: Жанр.
            tags: Список тегов.
            isbn: ISBN, если есть.
            pages: Количество страниц.

        Returns:
            Book: Экземпляр книги со сгенерированным ``id``.
        """
        return Book(
            id=str(uuid.uuid4()),
            title=title.strip(),
            author=author.strip(),
            year=int(year) if year is not None else None,
            genre=genre.strip() if genre else None,
            tags=[t.strip() for t in (tags or []) if t.strip()],
            isbn=isbn.strip() if isbn else None,
            pages=int(pages) if pages is not None else None,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует книгу в словарь для сериализации.

        Returns:
            Dict[str, Any]: Словарь полей книги.
        """
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Book":
        """Создаёт книгу из словаря (например, прочитанного из JSON).

        Args:
            data: Словарь полей.

        Returns:
            Book: Восстановленный объект книги.
        """
        return Book(
            id=str(data.get("id") or uuid.uuid4()),
            title=data["title"],
            author=data["author"],
            year=int(data["year"]) if data.get("year") not in (None, "") else None,
            genre=data.get("genre"),
            tags=list(data.get("tags", [])),
            isbn=data.get("isbn"),
            pages=int(data["pages"]) if data.get("pages") not in (None, "") else None,
            quotes=list(data.get("quotes", [])),
            added_at=data.get("added_at") or _now_iso(),
        )
