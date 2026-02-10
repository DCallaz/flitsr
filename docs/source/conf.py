# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

project = 'flitsr'
copyright = '2025, Dylan Callaghan'
author = 'Dylan Callaghan'
release = '2.4.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'myst_parser',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinxarg.ext',
    'sphinx.ext.napoleon',
]
autosummary_generate = True  # Turn on sphinx.ext.autosummary

default_role = 'autolink'

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'
# html_static_path = ['_static']


def autodoc_skip_member(app, what, name, obj, skip, options):
    exclusions = ('__weakref__',  'get_parser',  # special-members
                  '__doc__', '__module__', '__dict__',  # undoc-members
                  )
    exclude = name in exclusions
    # return True if (skip or exclude) else None
    # Can interfere with subsequent skip functions.
    return True if exclude else None


def setup(app):
    app.connect('autodoc-skip-member', autodoc_skip_member)
