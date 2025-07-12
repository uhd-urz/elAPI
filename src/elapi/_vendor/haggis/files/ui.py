# -*- coding: utf-8 -*-

# haggis: a library of general purpose utilities
#
# Copyright (C) 2023  Joseph R. Fox-Rabinovitz <jfoxrabinovitz at gmail dot com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# Author: Joseph Fox-Rabinovitz <jfoxrabinovitz at gmail dot com>
# Version: 19 May 2021: Initial Coding

"""
Utilities for interacting with the file system with an optional
graphical user interface.

The GUI package is chosen based on a list of supported selections,
defaulting to tkinter. Currently, only PyQt and tkinter are supported.
"""

__all__ = ['get_existing_file']


from os.path import isdir, isfile
from warnings import warn


_UI_ORDER = ['pyqt', 'tkinter']


def _iter(i):
    if isinstance(i, str):
        return i,
    return i


for name in _UI_ORDER:
    try:
        if name == 'pyqt':
            try:
                from PyQt5.QtWidgets import QFileDialog
            except ImportError:
                from PyQt4.QtGui import QFileDialog

            def _fix(ext):
                """
                Convert extensions with missing '*.' into canonical form.
                """
                ext = str(ext)
                if ext.startswith('*.') or ext == '*':
                    return ext
                elif ext.startswith('.'):
                    return '*' + ext
                elif ext.startswith('*'):
                    return ext[0] + '.' + ext[1:]
                return '*.' + ext

            def _filters(seq, sep):
                """
                Join all fixed extensions in `seq` with `sep`.
                """
                return sep.join(map(_fix, _iter(seq)))

            def _filt2str(item):
                """
                Create a Qt-compatible filter string based on a 2-element
                sequence containing a label and sequence of extensions.
                """
                return f'{item[0]} ({_filters(item[1], " ")})'

            def _filt2qt(filt, sel):
                """
                Convert a filter from `open_file` to Qt-suitable format.
                """
                if not filt:
                    return None, None

                try:
                    filtee = filt.items()
                    s = _filt2str((sel, filt[sel]))
                except AttributeError:
                    filtee = filt
                    s = _filt2str(filt[sel])
                return ';;'.join(map(_filt2str, filtee)), s

            def open_file(dir, title, filters=(), sel=0):
                """
                Qt implementation of the `open_file` interface.
                """
                filters, sel = _filt2qt(filters, sel)
                name, _ = QFileDialog.getOpenFileName(
                    None, title, dir, filters, sel
                )
                return name

        elif name == 'tkinter':
            from tkinter import Tk
            from tkinter.filedialog import askopenfilename

            def _fix(ext):
                """
                Convert extensions with missing '*.' into canonical form.
                """
                ext = str(ext)
                if ext.startswith('*.') or ext == '*':
                    return ext
                elif ext.startswith('.'):
                    return '*' + ext
                elif ext.startswith('*'):
                    return ext[0] + '.' + ext[1:]
                return '*.' + ext

            def _filt2tk(filt):
                """
                Convert a filter from `open_file` to Tk-suitable format.
                """
                if not filt:
                    return []

                try:
                    filtee = filt.items()
                except AttributeError:
                    filtee = filt
                return [(key, _fix(elem)) for key, value in filtee for elem in _iter(value)]

            def open_file(dir, title, filters=(), sel=0):
                """
                Tkinter implementation of the `open_file` interface.
                """
                filters = _filt2tk(filters)
                Tk().withdraw()
                return askopenfilename(
                    parent=None, title=title, initialdir=dir,
                    filetypes=filters
                )
    except ImportError:
        continue
    else:
        break
else:
    warn('No GUI package imported. All functions will fail.')

    def open_file(*args, **kwargs):
        raise TypeError('No supporting GUI package found')


def get_existing_file(filename=None, title='Open', filters=None, sel=0):
    """
    Return the name of an existing file.

    The file can be opened for reading unless permissions intervene.

    Parameters
    ----------
    filename : str, optional
        The initial file name to check. If the name exists and is a
        file, a GUI will not be displayed. If it is a directory, it will
        be used as the starting point in the GUI. The default is None.
    title : str or None
        An optional title for the dialog that will be displayed if
        `filename` does not exist.
    filters : sequence[str or tuple] or None
        A sequence or mapping of filename filters. Sequences must
        consist of two-tuples with a filter name and a list of
        extensions. Mappings contain a list of extensions as values. If
        None, no filtering will be done in the dialog. Filter extensions
        may contain a leading ``'*.'``, but are not required to contain
        either character.
    sel : str or int
        An optional key into `filters`, ignored if `filters` is None.

    Returns
    -------
    filename : str or None
        The name of an existing file, or None if the user changes their
        mind.
    """
    if filename is None:
        start = '.'
    else:
        if isfile(filename):
            return filename
        if isdir(filename):
            start = filename
        else:
            start = '.'

    return open_file(dir=start, title=title, filters=filters, sel=sel)
