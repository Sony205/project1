import argparse
from booklib.storage import DEFAULT_PATH
from booklib.commands_migrate import cmd_migrate_sqlite

def build_parser():
    p = argparse.ArgumentParser(prog="booklib-migrate", description="Миграция JSON → SQLite")
    p.add_argument('--src', default=str(DEFAULT_PATH), help='исходный JSON (по умолчанию ./library.json)')
    p.add_argument('--dst', default='library.db', help='целевой SQLite (по умолчанию library.db)')
    return p

def main():
    p = build_parser()
    args = p.parse_args()
    cmd_migrate_sqlite(args, None)

if __name__ == "__main__":
    main()
