"""Фильтры поиска и сортировки."""
from __future__ import annotations
from typing import List, Iterable, Optional
from .models import Book

def _norm(s: Optional[str]) -> str:
    """Нормализует строку (lower+trim).

    Args:
        s: Входная строка.
    Returns:
        str: Нормализованный вариант.
    """
    return (s or '').casefold().strip()

def search(
    books: Iterable[Book],
    query: Optional[str] = None,
    author: Optional[str] = None,
    title: Optional[str] = None,
    year: Optional[int] = None,
    genre: Optional[str] = None,
    tag: Optional[str] = None,
    isbn: Optional[str] = None,
    exact: bool = False,
) -> List[Book]:
    """Выполняет поиск по коллекции книг.

    Args:
        books: Коллекция книг.
        query: Общая строка поиска (по автору и названию).
        author: Автор.
        title: Название.
        year: Год издания.
        genre: Жанр.
        tag: Тег (ищется среди списка тегов).
        isbn: ISBN.
        exact: Если ``True``, строки сравниваются строго (без подстрок).

    Returns:
        list[Book]: Отфильтрованные книги.
    """
    q = _norm(query); a = _norm(author); t = _norm(title)
    g = _norm(genre); tg = _norm(tag); i = _norm(isbn)

    def match(b: Book) -> bool:
        if q and q not in _norm(b.author) and q not in _norm(b.title):
            return False
        if a:
            if (exact and a != _norm(b.author)) or (not exact and a not in _norm(b.author)):
                return False
        if t:
            if (exact and t != _norm(b.title)) or (not exact and t not in _norm(b.title)):
                return False
        if year is not None and b.year != year:
            return False
        if g:
            if (exact and g != _norm(b.genre)) or (not exact and g not in _norm(b.genre)):
                return False
        if tg:
            tags_norm = ' '.join(_norm(x) for x in (b.tags or []))
            if (exact and tg not in (_norm(x) for x in (b.tags or []))) or (not exact and tg not in tags_norm):
                return False
        if i:
            if (exact and i != _norm(b.isbn)) or (not exact and i not in _norm(b.isbn)):
                return False
        return True

    return [b for b in books if match(b)]

def sort_books(
    books: Iterable[Book],
    by: str = 'title',
    reverse: bool = False,
    secondary: Optional[str] = None,
) -> List[Book]:
    """Сортирует книги по указанному полю с необязательным вторичным ключом.

    Args:
        books: Коллекция книг.
        by: Поле сортировки (``title``, ``author``, ``year``, ``genre``, ``added_at``).
        reverse: Обратный порядок.
        secondary: Вторичное поле сортировки (или ``None``).

    Returns:
        list[Book]: Отсортированный список.
    """
    valid = {'title','author','year','genre','added_at'}
    if by not in valid:
        by = 'title'
    if secondary and secondary not in valid:
        secondary = None

    def keyfunc(b: Book):
        def norm(v): return (1, '') if v is None else (0, str(v).casefold())
        primary = getattr(b, by, None)
        secondary_val = getattr(b, secondary, None) if secondary else None
        k = (norm(primary),)
        if secondary is not None:
            k += (norm(secondary_val),)
        return k

    return sorted(list(books), key=keyfunc, reverse=reverse)
