"""CLI‑обёртка для книжной библиотеки `booklib`.

Точка входа для консольной утилиты ``booklib``. Здесь собирается
``argparse``‑парсер и выбирается тип хранилища (JSON или SQLite).
"""
import argparse
from pathlib import Path
from booklib import commands as C
from booklib.commands_migrate import cmd_migrate_sqlite
from booklib.storage import Storage, DEFAULT_PATH


def get_storage_for(db_path: str | None):
    """Возвращает подходящее хранилище по пути к базе данных.

    Если расширение файла указывает на SQLite (``.db``, ``.sqlite``,
    ``.sqlite3``), используется :class:`SqliteStorage`, иначе — JSON‑хранилище.

    Args:
        db_path: Путь к файлу базы данных или ``None``, если путь не задан.

    Returns:
        Объект хранилища, реализующий тот же интерфейс, что и :class:`Storage`.
    """
    if db_path:
        ext = Path(db_path).suffix.lower()
        if ext in {'.db', '.sqlite', '.sqlite3'}:
            from booklib.storage_sqlite import SqliteStorage
            return SqliteStorage(db_path)
        return Storage(db_path)
    return Storage()



def build_parser() -> argparse.ArgumentParser:
    """Строит и настраивает ``argparse``‑парсер для CLI.

    Создаёт корневой парсер ``booklib`` и регистрирует подкоманды:

    * ``add`` — добавление книги;
    * ``list`` — вывод списка книг с фильтрами и сортировкой;
    * ``find`` — поиск книг;
    * ``sort`` — сортировка без фильтрации;
    * ``show`` — подробная информация по одной книге;
    * ``update`` — изменение полей книги;
    * ``remove`` — удаление книги;
    * ``add-quote`` / ``del-quote`` — работа с цитатами;
    * ``export-csv`` / ``import-csv`` — экспорт/импорт в CSV;
    * ``migrate-sqlite`` — перенос базы из JSON в SQLite.

    Returns:
        argparse.ArgumentParser: настроенный парсер командной строки.
    """
    p = argparse.ArgumentParser(
        prog="booklib",
        description="Книжная библиотека: добавление книг, поиск и цитаты.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "--db",
        default=str(DEFAULT_PATH),
        help="путь к базе (JSON или SQLite). По умолчанию %(default)s",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    # --- Вспомогательные функции настройки общих аргументов ---

    def add_search_args(sp: argparse.ArgumentParser) -> None:
        """Добавляет к подкоманде аргументы фильтрации/поиска."""
        sp.add_argument(
            "-q",
            "--query",
            help="общий текстовый поиск по автору, названию и тегам",
        )
        sp.add_argument("--author", help="фильтр по автору")
        sp.add_argument("--title", help="фильтр по названию книги")
        sp.add_argument("--year", type=int, help="фильтр по году издания")
        sp.add_argument("--genre", help="фильтр по жанру")
        sp.add_argument("--tag", help="фильтр по тегу")
        sp.add_argument("--isbn", help="фильтр по ISBN")
        sp.add_argument(
            "--exact",
            action="store_true",
            help="точное совпадение полей вместо поиска по подстроке",
        )

    def add_sort_args(
        sp: argparse.ArgumentParser,
        *,
        with_long: bool = False,
    ) -> None:
        """Добавляет к подкоманде аргументы сортировки/формата вывода."""
        sp.add_argument(
            "--by",
            help="поле сортировки: title, author, year, genre, added_at",
        )
        sp.add_argument(
            "--secondary",
            help="вторичное поле сортировки (как и для --by)",
        )
        sp.add_argument(
            "--desc",
            action="store_true",
            help="сортировать в обратном порядке",
        )
        sp.add_argument(
            "--limit",
            type=int,
            help="ограничить количество выводимых записей",
        )
        if with_long:
            sp.add_argument(
                "--long",
                action="store_true",
                help="показывать подробную информацию по каждой книге",
            )

    # --- Команды ---

    # add
    sp = sub.add_parser(
        "add",
        help="добавить новую книгу",
        description="Добавляет книгу в JSON/SQLite‑базу.",
    )
    sp.add_argument(
        "-t",
        "--title",
        required=True,
        help="название книги",
    )
    sp.add_argument(
        "-a",
        "--author",
        required=True,
        help="автор книги",
    )
    sp.add_argument(
        "--year",
        type=int,
        help="год издания",
    )
    sp.add_argument(
        "--genre",
        help="жанр книги",
    )
    sp.add_argument(
        "--tags",
        nargs="*",
        help="список тегов (через пробел)",
    )
    sp.add_argument(
        "--isbn",
        help="ISBN книги",
    )
    sp.add_argument(
        "--pages",
        type=int,
        help="количество страниц",
    )
    sp.set_defaults(func=C.cmd_add)

    # list
    sp = sub.add_parser(
        "list",
        help="показать список книг",
        description="Выводит список книг с опциональным поиском и сортировкой.",
    )
    add_search_args(sp)
    add_sort_args(sp, with_long=True)
    sp.set_defaults(func=C.cmd_list)

    # find
    sp = sub.add_parser(
        "find",
        help="найти книги по условиям",
        description="Поиск книг по фильтрам и вывод результатов.",
    )
    add_search_args(sp)
    add_sort_args(sp, with_long=False)
    sp.set_defaults(func=C.cmd_find)

    # sort
    sp = sub.add_parser(
        "sort",
        help="отсортировать все книги",
        description="Выводит все книги, отсортированные по указанному полю.",
    )
    add_sort_args(sp, with_long=False)
    sp.set_defaults(func=C.cmd_sort)

    # show
    sp = sub.add_parser(
        "show",
        help="показать подробную информацию по книге",
    )
    sp.add_argument(
        "id",
        help="идентификатор книги (можно укороченный UUID)",
    )
    sp.set_defaults(func=C.cmd_show)

    # update
    sp = sub.add_parser(
        "update",
        help="обновить поля книги",
        description="Изменяет поля существующей книги по её идентификатору.",
    )
    sp.add_argument("id", help="идентификатор книги")
    sp.add_argument("--title", help="новое название")
    sp.add_argument("--author", help="новый автор")
    sp.add_argument("--year", type=int, help="новый год издания")
    sp.add_argument("--genre", help="новый жанр")
    sp.add_argument(
        "--tags",
        nargs="*",
        help="полный новый список тегов (перезаписывает старые)",
    )
    sp.add_argument("--isbn", help="новый ISBN")
    sp.add_argument("--pages", type=int, help="новое количество страниц")
    sp.set_defaults(func=C.cmd_update)

    # remove
    sp = sub.add_parser(
        "remove",
        help="удалить книгу из библиотеки",
    )
    sp.add_argument("id", help="идентификатор книги")
    sp.set_defaults(func=C.cmd_remove)

    # add-quote
    sp = sub.add_parser(
        "add-quote",
        help="добавить цитату к книге",
    )
    sp.add_argument("id", help="идентификатор книги")
    sp.add_argument("text", help="текст цитаты")
    sp.set_defaults(func=C.cmd_add_quote)

    # del-quote
    sp = sub.add_parser(
        "del-quote",
        help="удалить цитату из книги",
    )
    sp.add_argument("id", help="идентификатор книги")
    sp.add_argument(
        "index",
        type=int,
        help="номер цитаты (начиная с 1)",
    )
    sp.set_defaults(func=C.cmd_del_quote)

    # export-csv
    sp = sub.add_parser(
        "export-csv",
        help="экспортировать базу в CSV‑файл",
    )
    sp.add_argument(
        "path",
        help="путь к CSV‑файлу, в который будет выполнен экспорт",
    )
    sp.set_defaults(func=C.cmd_export_csv)

    # import-csv
    sp = sub.add_parser(
        "import-csv",
        help="импортировать записи из CSV‑файла",
    )
    sp.add_argument(
        "path",
        help="путь к CSV‑файлу с данными книг",
    )
    sp.set_defaults(func=C.cmd_import_csv)

    # migrate-sqlite
    sp = sub.add_parser(
        "migrate-sqlite",
        help="миграция JSON → SQLite",
        description="Создаёт SQLite‑базу и копирует в неё данные из JSON‑файла.",
    )
    sp.add_argument(
        "--src",
        default=str(DEFAULT_PATH),
        help="исходный JSON (по умолчанию %(default)s)",
    )
    sp.add_argument(
        "--dst",
        default="library.db",
        help="целевой SQLite‑файл (по умолчанию %(default)s)",
    )
    sp.set_defaults(func=cmd_migrate_sqlite)

    return p


def main():
    """Точка входа для запуска из консоли.

    Разбирает аргументы командной строки, создаёт подходящее хранилище и
    передаёт управление выбранной подкоманде.
    """
    p = build_parser()
    args = p.parse_args()
    storage = get_storage_for(args.db)
    args.func(args, storage)


if __name__ == "__main__":
    main()
