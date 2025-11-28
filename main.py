import argparse
from pathlib import Path
from booklib import commands as C
from booklib.commands_migrate import cmd_migrate_sqlite
from booklib.storage import Storage, DEFAULT_PATH

def get_storage_for(db_path: str | None):
    if db_path:
        ext = Path(db_path).suffix.lower()
        if ext in {'.db', '.sqlite', '.sqlite3'}:
            from booklib.storage_sqlite import SqliteStorage
            return SqliteStorage(db_path)
        return Storage(db_path)
    return Storage()

def build_parser():
    p = argparse.ArgumentParser(prog="booklib")
    p.add_argument("--db", help="путь к базе (JSON или SQLite). По умолчанию ./library.json")
    sub = p.add_subparsers(dest="cmd", required=True)

    # существующие команды (объявляем, чтобы связать с вашим commands.py)
    sub.add_parser("add").set_defaults(func=C.cmd_add)
    sub.add_parser("list").set_defaults(func=C.cmd_list)
    sub.add_parser("find").set_defaults(func=C.cmd_find)
    sub.add_parser("sort").set_defaults(func=C.cmd_sort)
    sub.add_parser("show").set_defaults(func=C.cmd_show)
    sub.add_parser("update").set_defaults(func=C.cmd_update)
    sub.add_parser("remove").set_defaults(func=C.cmd_remove)
    sub.add_parser("add-quote").set_defaults(func=C.cmd_add_quote)
    sub.add_parser("del-quote").set_defaults(func=C.cmd_del_quote)
    sub.add_parser("export-csv").set_defaults(func=C.cmd_export_csv)
    sub.add_parser("import-csv").set_defaults(func=C.cmd_import_csv)

    # новая команда миграции
    sp = sub.add_parser('migrate-sqlite', help='миграция JSON -> SQLite')
    sp.add_argument('--src', default=str(DEFAULT_PATH),
                    help='исходный JSON (по умолчанию ./library.json)')
    sp.add_argument('--dst', default='library.db',
                    help='целевой SQLite (по умолчанию library.db)')
    sp.set_defaults(func=cmd_migrate_sqlite)
    return p

def main():
    p = build_parser()
    args = p.parse_args()
    storage = get_storage_for(args.db)
    args.func(args, storage)

if __name__ == "__main__":
    main()
