Быстрый старт
============

Установка зависимостей::

    pip install -r requirements.txt

Запуск::

    python main.py --help
    python main.py add -t "Название" -a "Автор"
    python main.py list --long

Генерация документации Sphinx::

    cd docs
    sphinx-build -b html . _build/html
