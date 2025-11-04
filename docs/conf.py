# -- Конфигурация Sphinx -------------------------------------------------
import os, sys
from datetime import datetime

# Путь к проекту (родитель каталога docs)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

project = 'booklib'
author = 'booklib authors'
copyright = f'{datetime.utcnow():%Y}, {author}'
release = '1.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_use_param = True
napoleon_use_rtype = True

templates_path = ['_templates']
exclude_patterns = []

html_theme = 'alabaster'
html_static_path = ['_static']
