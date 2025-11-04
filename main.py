"""Точка входа CLI-приложения `booklib`.

Поддерживаемые команды см. ``booklib --help``. Для генерации документации
используется Sphinx (``docs/``).
"""
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from booklib.storage import Storage
from booklib import commands as C

def positive_int(val: str) -> int:
    """Проверяет, что число положительное (>0).

    Args:
        val: Строка с целым числом.
    Returns:
        int: Значение, преобразованное к int.
    Raises:
        argparse.ArgumentTypeError: Если число <= 0.
    """
    x = int(val)
    if x <= 0:
        raise argparse.ArgumentTypeError('должно быть > 0')
    return x

def build_parser() -> argparse.ArgumentParser:
    """Создаёт парсер аргументов командной строки.

    Returns:
        argparse.ArgumentParser: Сконфигурированный парсер.
    """
    p = argparse.ArgumentParser(prog='booklib', description='Домашняя книжная библиотека (CLI)')
    p.add_argument('--db', help='путь к JSON-файлу (по умолчанию рядом с main.py: library.json)')
    sub = p.add_subparsers(dest='cmd', required=True)

    sp = sub.add_parser('add', help='добавить книгу')
    sp.add_argument('-t','--title', required=True, help='название')
    sp.add_argument('-a','--author', required=True, help='автор')
    sp.add_argument('-y','--year', type=int, help='год')
    sp.add_argument('-g','--genre', help='жанр')
    sp.add_argument('-T','--tags', nargs='*', default=[], help='теги (через пробел)')
    sp.add_argument('--isbn', help='ISBN')
    sp.add_argument('--pages', type=int, help='число страниц')
    sp.set_defaults(func=C.cmd_add)

    sp = sub.add_parser('list', help='список книг')
    sp.add_argument('--by', choices=['title','author','year','genre','added_at'], default='title', help='поле сортировки')
    sp.add_argument('--secondary', choices=['title','author','year','genre','added_at'], help='вторичное поле сортировки')
    sp.add_argument('--desc', action='store_true', help='убывающий порядок')
    sp.add_argument('--limit', type=positive_int, help='ограничить вывод')
    sp.add_argument('--long', action='store_true', help='подробный вывод')
    sp.add_argument('-q','--query', help='общий поиск по автору/названию')
    sp.add_argument('--author', help='поиск по автору')
    sp.add_argument('--title', help='поиск по названию')
    sp.add_argument('--year', type=int, help='поиск по году')
    sp.add_argument('--genre', help='по жанру')
    sp.add_argument('--tag', help='по тегу')
    sp.add_argument('--isbn', help='поиск по ISBN')
    sp.add_argument('--exact', action='store_true', help='точное совпадение строк')
    sp.set_defaults(func=C.cmd_list)

    sp = sub.add_parser('find', help='поиск книг')
    sp.add_argument('-q','--query', help='общий поиск по автору/названию')
    sp.add_argument('--author', help='по автору')
    sp.add_argument('--title', help='по названию')
    sp.add_argument('--year', type=int, help='по году')
    sp.add_argument('--genre', help='по жанру')
    sp.add_argument('--tag', help='по тегу')
    sp.add_argument('--isbn', help='по ISBN')
    sp.add_argument('--exact', action='store_true', help='точное совпадение строк')
    sp.add_argument('--by', choices=['title','author','year','genre','added_at'], default='title', help='сортировка')
    sp.add_argument('--secondary', choices=['title','author','year','genre','added_at'], help='вторичное поле')
    sp.add_argument('--desc', action='store_true', help='убывающий порядок')
    sp.add_argument('--limit', type=positive_int, help='ограничить вывод')
    sp.set_defaults(func=C.cmd_find)

    sp = sub.add_parser('sort', help='отсортировать и показать')
    sp.add_argument('--by', choices=['title','author','year','genre','added_at'], default='title')
    sp.add_argument('--secondary', choices=['title','author','year','genre','added_at'], help='вторичное поле')
    sp.add_argument('--desc', action='store_true')
    sp.add_argument('--limit', type=positive_int, help='ограничить вывод')
    sp.set_defaults(func=C.cmd_sort)

    sp = sub.add_parser('show', help='показать книгу подробно')
    sp.add_argument('id', help='UUID или префикс (можно без скобок)')
    sp.set_defaults(func=C.cmd_show)

    sp = sub.add_parser('update', help='обновить поля книги')
    sp.add_argument('id', help='UUID или префикс (можно без скобок)')
    sp.add_argument('-t','--title', help='название')
    sp.add_argument('-a','--author', help='автор')
    sp.add_argument('-y','--year', type=int, help='год')
    sp.add_argument('-g','--genre', help='жанр')
    sp.add_argument('-T','--tags', nargs='*', help='теги (перезапишут список)')
    sp.add_argument('--isbn', help='ISBN')
    sp.add_argument('--pages', type=int, help='число страниц')
    sp.set_defaults(func=C.cmd_update)

    sp = sub.add_parser('remove', help='удалить книгу')
    sp.add_argument('id', help='UUID или префикс (можно без скобок)')
    sp.set_defaults(func=C.cmd_remove)

    sp = sub.add_parser('add-quote', help='добавить цитату к книге')
    sp.add_argument('id', help='UUID или префикс (можно без скобок)')
    sp.add_argument('text', help='текст цитаты')
    sp.set_defaults(func=C.cmd_add_quote)

    sp = sub.add_parser('del-quote', help='удалить цитату по индексу (1..n)')
    sp.add_argument('id', help='UUID или префикс (можно без скобок)')
    sp.add_argument('index', type=int, help='индекс цитаты (1..n)')
    sp.set_defaults(func=C.cmd_del_quote)

    sp = sub.add_parser('export-csv', help='экспорт в CSV')
    sp.add_argument('path', help='путь к CSV')
    sp.set_defaults(func=C.cmd_export_csv)

    sp = sub.add_parser('import-csv', help='импорт из CSV')
    sp.add_argument('path', help='путь к CSV')
    sp.set_defaults(func=C.cmd_import_csv)

    return p

def main(argv=None):
    """Запускает парсер и делегирует выполнение выбранной команде."""
    parser = build_parser()
    args = parser.parse_args(argv)
    storage = Storage(args.db) if args.db else Storage()
    return args.func(args, storage)

if __name__ == '__main__':
    main()
