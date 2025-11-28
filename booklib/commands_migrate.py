"""Отдельный обработчик миграции JSON → SQLite, чтобы не править ваш commands.py."""
def cmd_migrate_sqlite(args, _storage):
    """
    Перенос всех записей из JSON (args.src) в SQLite (args.dst).
    Текущий _storage игнорируется специально.
    """
    from .storage import Storage as JsonStorage
    from .storage_sqlite import SqliteStorage
    js = JsonStorage(args.src)
    sq = SqliteStorage(args.dst)
    books = js.load()
    sq.save(books)
    print(f"Миграция завершена: {len(books)} записей → {args.dst}")
