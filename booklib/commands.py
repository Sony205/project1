from __future__ import annotations
from typing import List, Optional
import re
from .models import Book
from .storage import Storage
from .filters import search, sort_books

def _print_table(books: List[Book], limit: Optional[int] = None) -> None:
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
    return (s or '').strip().casefold()

def _dedupe_keep_order(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for it in items or []:
        key = _norm_ci(it)
        if key not in seen:
            seen.add(key)
            out.append(it)
    return out

def _clean_id(s: str) -> str:
    return (s or '').strip().strip('[]{}()')

def _resolve_id(storage: Storage, user_id: str) -> Optional[str]:
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
    books = storage.load()
    books = sort_books(books, by=args.by, reverse=args.desc, secondary=args.secondary)
    _print_table(books, limit=args.limit)

def cmd_show(args, storage: Storage):
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

def _equal_tags(a, b):
    return [_norm_ci(x) for x in (a or [])] == [_norm_ci(x) for x in (b or [])]

def cmd_update(args, storage: Storage):
    rid = _resolve_id(storage, args.id)
    if not rid:
        return
    b = storage.get(rid)
    if not b:
        print('Книга не найдена.')
        return

    notes: List[str] = []
    changed = False

    # --- genre ---
    if args.genre is not None:
        if b.genre is not None and _norm_ci(b.genre) == _norm_ci(args.genre):
            notes.append(f'Жанр «{args.genre}» уже был установлен ранее.')
        else:
            b.genre = args.genre
            changed = True

    # --- pages ---
    if args.pages is not None:
        if b.pages is not None and b.pages == args.pages:
            notes.append(f'Число страниц {args.pages} уже было установлено ранее.')
        else:
            b.pages = args.pages
            changed = True

    # --- tags (перезапись списка, но только если он реально изменился) ---
    if args.tags is not None:
        provided = _dedupe_keep_order(args.tags)
        if _equal_tags(b.tags, provided):
            notes.append('Список тегов не изменился: ' + ', '.join(provided))
        else:
            # Дополнительно сообщим, какие из переданных уже были
            existed_norm = {_norm_ci(t) for t in (b.tags or [])}
            already = [t for t in provided if _norm_ci(t) in existed_norm]
            if already:
                notes.append('Теги уже были: ' + ', '.join(already))
            b.tags = provided
            changed = True

    # --- остальные поля ---
    if args.title is not None:
        if _norm_ci(b.title) == _norm_ci(args.title):
            notes.append('Название не изменилось.')
        else:
            b.title = args.title
            changed = True

    if args.author is not None:
        if _norm_ci(b.author) == _norm_ci(args.author):
            notes.append('Автор не изменился.')
        else:
            b.author = args.author
            changed = True

    if args.year is not None:
        if b.year == args.year:
            notes.append(f'Год {args.year} уже был установлен ранее.')
        else:
            b.year = args.year
            changed = True

    if args.isbn is not None:
        if _norm_ci(b.isbn) == _norm_ci(args.isbn):
            notes.append('ISBN не изменился.')
        else:
            b.isbn = args.isbn
            changed = True

    if changed:
        storage.update(b)
        print('Книга обновлена.')
    else:
        print('Изменений нет.')

    for line in notes:
        print('  • ' + line)

def cmd_remove(args, storage: Storage):
    rid = _resolve_id(storage, args.id)
    if not rid:
        return
    ok = storage.delete(rid)
    print('Удалено.' if ok else 'Книга не найдена.')

def _norm_quote(s: str) -> str:
    return re.sub(r'\s+', ' ', (s or '')).strip().casefold()

def cmd_add_quote(args, storage: Storage):
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
    n = storage.export_csv(args.path)
    print(f'Экспортировано записей: {n} → {args.path}')

def cmd_import_csv(args, storage: Storage):
    n = storage.import_csv(args.path)
    print(f'Импортировано/обновлено записей: {n} (дубликаты пропущены)')
