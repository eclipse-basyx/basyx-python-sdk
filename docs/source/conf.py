# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
import datetime
from sphinx.ext import intersphinx


sys.path.insert(0, os.path.abspath('../..'))
from basyx.aas import __version__


# -- Project information -----------------------------------------------------

project = 'Eclipse BaSyx Python SDK'
project_copyright = str(datetime.datetime.now().year) + ', the Eclipse BaSyx Authors'
author = 'The Eclipse BaSyx Authors'

# The full version, including alpha/beta/rc tags
release = __version__


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.coverage',
    'sphinx.ext.intersphinx',
    'sphinx_rtd_theme',
    'sphinxarg.ext'
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# Don't prepend the name of the current module to all classes.
add_module_names = False

# Include all public documented and undocumented members by default.
autodoc_default_options = {
    'members': True,
    'undoc-members': True
}

# Mapping for correctly linking other module documentations.
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'dateutil': ('https://dateutil.readthedocs.io/en/stable/', None),
    'lxml': ('https://lxml.de/apidoc/', None)
}


def on_missing_reference(app, env, node, contnode):
    path = node["reftarget"].split(".")
    # lxml uses _Element instead of Element and _ElementTree instead of ElementTree in its documentation,
    # causing missing references if untreated.
    if len(path) > 2 and path[0:2] == ["lxml", "etree"] and path[2] in {"Element", "ElementTree"}:
        node["reftarget"] = ".".join(path[0:2] + ["_" + path[2]] + path[3:])
        return intersphinx.resolve_reference_in_inventory(env, "lxml", node, contnode)
    return None


def setup(app):
    app.connect("missing-reference", on_missing_reference)


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = []
