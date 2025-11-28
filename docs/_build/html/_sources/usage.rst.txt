Быстрый старт
=============

Установка зависимостей::

    pip install -r requirements.txt

Запуск::

    python main.py --help
    python main.py add -t "Название" -a "Автор"
    python main.py list --long

Генерация документации Sphinx::

    cd docs
    sphinx-build -b html . _build/html

Использование SQLite
--------------------
По расширению пути `--db` выбирается бэкенд:
- `*.json` — JSON‑хранилище;
- `*.db`, `*.sqlite`, `*.sqlite3` — SQLite.

Примеры::
    python main.py --db library.db add -t "Название" -a "Автор"
    python main.py --db library.db list --long

Миграция из JSON в SQLite::
    python main.py migrate-sqlite --src library.json --dst library.db
