# booklib — CLI для домашней библиотеки (с докстрингами и Sphinx)

* Докстринги в стиле Google на всех модулях/функциях/классах.
* База по умолчанию: `./library.json` рядом с `main.py`.
* Sphinx-конфигурация в `docs/` (`autodoc`, `napoleon`, `viewcode`).

## Проверка docstring через `help()`
```python
from booklib.storage import Storage
help(Storage)

from booklib.models import Book
help(Book.create)
```

## Генерация документации
```bash
pip install -r requirements.txt
cd docs
sphinx-build -b html . _build/html
# или
make html           # Linux/Mac
.\make.bat html     # Windows
```
