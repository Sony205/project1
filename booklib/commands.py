"""Обработчики команд CLI для `booklib`.

Каждая функция ``cmd_*`` привязана к подкоманде argparse в :mod:`main`.
"""
from __future__ import annotations
from typing import List, Optional
import re
from .models import Book
from .storage import Storage
from .filters import search, sort_books

def _print_table(books: List[Book], limit: Optional[int] = None) -> None:
    """Печатает таблицу с краткой информацией о книгах.

    Args:
        books: Список книг.
        limit: Максимальное количество выводимых записей (или ``None``).
    """
    rows = []
    subset = books[:limit] if limit else books
    for b in subset:
        rows.append([b.id[:8], b.title, b.author, b.year or '', b.genre or '', ', '.join(b.tags)])
    colw = [8, 28, 22, 6, 12, 24]
    headers = ['id', 'Название', 'Автор', 'Год', 'Жанр', 'Теги']
    def fmt_row(r):
        cells = []
        for i, cell in enumerate(r):
            s = str(cell)
            s = (s[: colw[i] - 1] + '…') if len(s) > colw[i] else s
            cells.append(s.ljust(colw[i]))
        return '  '.join(cells)
    print(fmt_row(headers))
    print('-' * (sum(colw) + 10))
    for r in rows:
        print(fmt_row(r))

# --- helpers ---
def _norm_ci(s: str) -> str:
    """Нормализует строку (lower+trim) для case-insensitive сравнения."""
    return (s or '').strip().casefold()

def _dedupe_keep_order(items: List[str]) -> List[str]:
    """Удаляет дубли из списка тегов, сохраняя порядок.

    Args:
        items: Исходные элементы.
    Returns:
        list[str]: Список без дубликатов.
    """
    seen = set()
    out = []
    for it in items or []:
        key = _norm_ci(it)
        if key not in seen:
            seen.add(key)
            out.append(it)
    return out

def _clean_id(s: str) -> str:
    """Очищает идентификатор от пробелов и скобок ([], {}, ())."""
    return (s or '').strip().strip('[]{}()')

def _resolve_id(storage: Storage, user_id: str) -> Optional[str]:
    """Разрешает введённый идентификатор в полный UUID.

    Поддерживаются префиксы (первые символы UUID) и идентификаторы со скобками.

    Args:
        storage: Экземпляр хранилища.
        user_id: Введённый пользователем UUID или его префикс.

    Returns:
        Optional[str]: Полный UUID или ``None``, если найти однозначно не удалось.
    """
    wanted = _clean_id(user_id)
    books = storage.load()
    if len(wanted) >= 36:
        return wanted
    matches = [b for b in books if b.id.startswith(wanted)]
    if len(matches) == 1:
        return matches[0].id
    if not matches:
        print('Книга не найдена.')
        return None
    print('Найдено несколько совпадений по префиксу, уточните ID:')
    for b in matches:
        print(f'  {b.id} — {b.title} / {b.author}')
    return None

# --- commands ---
def cmd_add(args, storage: Storage):
    """Добавляет книгу из аргументов командной строки."""
    book = Book.create(
        title=args.title, author=args.author, year=args.year,
        genre=args.genre, tags=args.tags, isbn=args.isbn, pages=args.pages
    )
    ok, existing = storage.add(book)
    if ok:
        print(f'Добавлена книга: {book.title} ({book.author}), id={book.id}')
    else:
        msg = f'Пропущено: такая книга уже есть — {existing.title} ({existing.author})'
        if existing.year is not None:
            msg += f', {existing.year}'
        msg += f', id={existing.id}'
        print(msg)

def cmd_list(args, storage: Storage):
    """Выводит список книг (с опциональным поиском/сортировкой)."""
    books = storage.load()
    books = sort_books(books, by=args.by, reverse=args.desc, secondary=args.secondary)
    if args.query or args.author or args.title or args.year or args.genre or args.tag or args.isbn:
        books = search(
            books,
            query=args.query, author=args.author, title=args.title,
            year=args.year, genre=args.genre, tag=args.tag, isbn=args.isbn,
            exact=args.exact
        )
    if args.long:
        subset = books[:args.limit] if args.limit else books
        for b in subset:
            print(f'[{b.id}] {b.title} — {b.author} ({b.year or "n/a"}) [{b.genre or "—"}]')
            if b.tags:
                print('  Теги:', ', '.join(b.tags))
            if b.isbn:
                print('  ISBN:', b.isbn)
            if b.pages:
                print('  Страниц:', b.pages)
            if b.quotes:
                print('  Цитаты:', len(b.quotes))
            print('  Добавлено:', b.added_at)
            print('')
    else:
        _print_table(books, limit=args.limit)
        print(f'\nВсего: {len(books)}')

def cmd_find(args, storage: Storage):
    """Выполняет поиск и печатает результаты."""
    books = storage.load()
    res = search(
        books,
        query=args.query, author=args.author, title=args.title,
        year=args.year, genre=args.genre, tag=args.tag, isbn=args.isbn,
        exact=args.exact
    )
    res = sort_books(res, by=args.by, reverse=args.desc, secondary=args.secondary)
    if not res:
        print('Ничего не найдено.')
        return
    _print_table(res, limit=args.limit)
    print(f'\nНайдено: {len(res)}')

def cmd_sort(args, storage: Storage):
    """Сортирует и печатает список книг."""
    books = storage.load()
    books = sort_books(books, by=args.by, reverse=args.desc, secondary=args.secondary)
    _print_table(books, limit=args.limit)

def cmd_show(args, storage: Storage):
    """Показывает подробную информацию по книге."""
    rid = _resolve_id(storage, args.id)
    if not rid:
        return
    b = storage.get(rid)
    if not b:
        print('Книга не найдена.')
        return
    print(f'[{b.id}] {b.title} — {b.author}')
    print(f'Год: {b.year or "n/a"}; Жанр: {b.genre or "н/д"}')
    print(f'Теги: {", ".join(b.tags) if b.tags else "—"}')
    print(f'ISBN: {b.isbn or "—"}; Страниц: {b.pages or "—"}')
    print(f'Добавлено: {b.added_at}')
    print('Цитаты:')
    if not b.quotes:
        print('  —')
    else:
        for i, q in enumerate(b.quotes, 1):
            print(f'  {i:>2}. {q}')

def cmd_update(args, storage: Storage):
    """Обновляет поля книги. Поля, не указанные в аргументах, остаются без изменений."""
    rid = _resolve_id(storage, args.id)
    if not rid:
        return
    b = storage.get(rid)
    if not b:
        print('Книга не найдена.')
        return

    notes: List[str] = []

    if args.genre is not None:
        if b.genre is not None and _norm_ci(b.genre) == _norm_ci(args.genre):
            notes.append(f'Жанр «{args.genre}» уже был установлен ранее.')
        b.genre = args.genre

    if args.pages is not None:
        if b.pages is not None and b.pages == args.pages:
            notes.append(f'Число страниц {args.pages} уже было установлено ранее.')
        b.pages = args.pages

    if args.tags is not None:
        provided = _dedupe_keep_order(args.tags)
        existed_norm = {_norm_ci(t) for t in (b.tags or [])}
        already = [t for t in provided if _norm_ci(t) in existed_norm]
        if already:
            notes.append('Теги уже были: ' + ', '.join(already))
        b.tags = provided

    if args.title is not None:
        b.title = args.title
    if args.author is not None:
        b.author = args.author
    if args.year is not None:
        b.year = args.year
    if args.isbn is not None:
        b.isbn = args.isbn

    from_changed = storage.update(b)
    print('Книга обновлена.' if from_changed else 'Книга не найдена.')
    for line in notes:
        print('  • ' + line)

def cmd_remove(args, storage: Storage):
    """Удаляет книгу по UUID/префиксу."""
    rid = _resolve_id(storage, args.id)
    if not rid:
        return
    ok = storage.delete(rid)
    print('Удалено.' if ok else 'Книга не найдена.')

def _norm_quote(s: str) -> str:
    """Нормализует цитату (схлопывает пробелы и приводит к нижнему регистру)."""
    return re.sub(r'\s+', ' ', (s or '')).strip().casefold()

def cmd_add_quote(args, storage: Storage):
    """Добавляет цитату к книге (дубликаты игнорируются регистронезависимо)."""
    rid = _resolve_id(storage, args.id)
    if not rid:
        return
    b = storage.get(rid)
    if not b:
        print('Книга не найдена.')
        return
    quote = (args.text or '').strip()
    if not quote:
        print('Пустая цитата.')
        return
    norm_new = _norm_quote(quote)
    if any(_norm_quote(q) == norm_new for q in (b.quotes or [])):
        print('Пропущено: такая цитата уже есть.')
        return
    b.quotes.append(quote)
    storage.update(b)
    print('Цитата добавлена.')

def cmd_del_quote(args, storage: Storage):
    """Удаляет цитату по индексу (1..n) у указанной книги."""
    rid = _resolve_id(storage, args.id)
    if not rid:
        return
    b = storage.get(rid)
    if not b:
        print('Книга не найдена.')
        return
    idx = args.index
    if idx < 1 or idx > len(b.quotes):
        print('Неверный индекс цитаты.')
        return
    removed = b.quotes.pop(idx - 1)
    storage.update(b)
    print('Удалена цитата:', removed)

def cmd_export_csv(args, storage: Storage):
    """Экспортирует текущую базу в CSV."""
    n = storage.export_csv(args.path)
    print(f'Экспортировано записей: {n} → {args.path}')

def cmd_import_csv(args, storage: Storage):
    """Импортирует записи из CSV (см. :meth:`Storage.import_csv`)."""
    n = storage.import_csv(args.path)
    print(f'Импортировано/обновлено записей: {n} (дубликаты пропущены)')
