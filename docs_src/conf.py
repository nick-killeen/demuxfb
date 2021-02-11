# Configuration file for the Sphinx documentation builder.

# -- Path setup --------------------------------------------------------------

import re
import os
import sys
sys.path.insert(0, os.path.abspath('../src'))

# -- Project information -----------------------------------------------------

project = 'demuxfb'
copyright = '2021, Nicholas Killeen'  # pylint: disable=redefined-builtin
author = 'Nicholas Killeen'

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'm2r2',
]

default_role = 'py:obj'

# In the source files, there is duplicate information about class attributes:
# as a type hint (for IntelliSense and local documentation), and in the
# docstring (for building large front-facing docs). By default, autodoc picks
# up on both, which will cause duplicate entries in the output.
#
# So, where docstrings are present, 'skip' the type hint information. Where
# docstrings are not present, the type hint info should be left in.
names_to_skip = set()


def skip_member(_app, _what, name, obj, _would_skip, _options):
    global names_to_skip
    if name == '__doc__' and obj is not None:
        lines = obj.split('\n') + ['']
        stripped_lines = [s.strip() for s in lines]

        # Get where the 'Attributes' section starts, and its indentation level.
        first_attribute_pos = -1
        indentation = None
        for i in range(len(lines) - 1):
            if stripped_lines[i] == 'Attributes' and \
                    stripped_lines[i + 1] == '----------':
                indentation = ' ' * (len(lines[i]) - len(stripped_lines[i]))
                first_attribute_pos = i + 2
        if first_attribute_pos == -1:
            return None

        # Read attributes until this section ends.
        for i in range(first_attribute_pos, len(lines) - 1):
            if '-' * len(stripped_lines[i]) == stripped_lines[i + 1]:
                return None
            if stripped_lines[i] != '' and \
                    not lines[i].startswith(indentation + (' ' * 4)):
                names_to_skip.add(lines[i].split(':')[0].strip())
    elif name in names_to_skip:
        names_to_skip.remove(name)
        return True
    elif name == '__init__' and not obj.__doc__.lstrip().startswith(
            'This method should not be called publicly.'):
        return False
    return None


# Fix type hint displays: they are written to make sense locally rather than
# from a document generator's perspective, so we might write
#   demuxfb._participant.Participant
# where the outside world only knows of this type through
#   demuxfb.Participant.
# This processing sends the former to the latter.
#
# Note: this does not fix how base classes or members appear.
def process_signature(_app, _what, _name, _obj, _options, signature,
                      return_annotation):
    def sub(s):
        if s is None:
            return None
        return re.sub(r'demuxfb\.[a-zA-Z0-9_]+\.([a-zA-Z0-9][a-zA-Z0-9_]*)',
                      lambda match: 'demuxfb.' + match[1], s)

    return (sub(signature), sub(return_annotation))


def setup(app):
    app.connect('autodoc-skip-member', skip_member)
    app.connect('autodoc-process-signature', process_signature)


templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------

html_theme = 'haiku'

html_static_path = ['_static']
