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
# Version: 13 Apr 2019: Initial Coding

"""
Routines for dealing with file types.

The module names in this package generally correspond to the informal
name of the file type they deal with, or to the extension.
"""

__all__ = [
    'ensure_extension', 'insert_suffix', 'open_file', 'split_extension',
    'PreOpenedFile',
]


from os.path import splitext

from ..recipes import is_ordered_subset as _is_ordered_subset
from ..string_util import check_value


def ensure_extension(name, ext, partial_policy=None, partial_limit=None):
    """
    Verify that the name ends with the required extension, and
    update it if not.

    `name` is assumed to be a string. `ext` is the desired suffix,
    usually beginning with ``'.'``. If `name` aleady ends with `ext`,
    return it as-is. If not, the extension will either be appended or
    completed depending on `partial_policy` and `partial_limit`. The
    first character of `ext` is treated as the separator character. It
    must appear in `name` for any of the completions to work.

    Recognized values for `partial_policy` are as follows (case
    insensitive):

        :py:obj:`None`, ``'none'``, ``''``
            No partial extensions are recognized. If ``name='a.xls'``
            and ``ext='.xlsx'``, the result is ``'a.xls.xlsx'``.
            Similarly, for ``'b.jpg'``, ``'.jpeg'``, the result is
            ``'b.jpg.jpeg'``.
        ``'append'``, ``'+'``
            Existing extension can be extended by at most
            `partial_limit` characters to acheive the target. If
            ``name='a.xls'`` and ``ext='.xlsx'``, the result is
            ``'a.xlsx'``. However, for ``'b.jpg'``, ``'.jpeg'``, the
            result is ``'b.jpg.jpeg'``.
        ``'insert'``, ``'^'``
            Existing extension can have up to `partial_limit` characters
            inserted anywhere to achieve the target. If ``name='a.xls'``
            and ``ext='.xlsx'``, the result is ``'a.xlsx'``. Similarly,
            for ``'b.jpg'``, ``'.jpeg'``, the result is ``b.jpeg``.
        ``'strip'``, ``'-'``
            The existing extension may be loner than the desired one, so
            up to `partial_limit` characters may be stripped off the end
            to match the target. If ``name='a.xlsx'`` and
            ``ext='.xls'``, the result is ``'a.xls'``. However, for
            ``'b.jpeg'``, ``'.jpg'``, the result is ``'b.jpeg.jpg'``.
        ``'remove'``, ``'x'``
            The existing extension may be longer than the desired one,
            so removing up to `partial_limit` characters anywhere in the
            name is allowed. If ``name='b.jpeg'`` and ``ext='.jpg'``,
            the result is ``'b.jpg'``. However, for ``name='b.jpg'`` and
            ``ext='.jpeg'``, the result is ``'b.jpg.jpeg'``.
        ``'replace'``, ``'r'``
            Replace any existing extension with the provided one.
        ``'create'``, ``'c'``
            Create the extension only if one does not already exist.

    `partial_limit` determines the maximum number of characters that can
    be modified to achieve the target. If :py:obj:`None` or a number
    greater than the length of `ext` mean "any number". If zero, the
    result is the same as for `partial_policy='none'` regardless of the
    actual value of `partial_policy`, unless `partial_policy` is
    ``'replace'``, which completely ignores the limit.
    """
    if partial_policy is not None:
        partial_type = check_value(partial_policy, ensure_extension.policies,
                                   label='match policy')
    else:
        partial_type = None

    if name.endswith(ext):
        # This should handle the empty `ext` case as well
        return name

    # At this point, `ext` is guarantee to be non-empty
    index = name.rfind(ext[0])

    if index == -1 or partial_type in (None, '', 'none'):
        return name + ext
    # At this point, `name` is guaranteed to contain `ext[0]` at index

    if partial_type in ('create', 'c'):
        return name

    def right_size(longer=True):
        """
        True if `partial_limit` is `None`, or if `ext` at least as long
        as the suffix of `name`, but by no more than `partial_limit`
        characters. This means that the name can be appended/inserted to
        to get the desired extension.

        If `longer` is `False`, the sense of the comparison is reversed:
        `ext` must be shorter than the suffix so the name can be
        stripped/removed from to get the extension.
        """
        delta = len(ext) - (last - index)
        if not longer:
            delta = -delta
        return partial_limit is None or 0 <= delta <= partial_limit

    last = len(name) - 1
    replace = False
    if partial_type in ('append', '+'):
        if right_size(True) and ext.startswith(name[index:]):
            replace = True
    elif partial_type in ('insert', '^'):
        if right_size(True) and _is_ordered_subset(name[index:], ext):
            replace = True
    elif partial_type in ('strip', '-'):
        if right_size(False) and name[index:].startswith(ext):
            replace = True
    elif partial_type in ('remove', 'x'):
        if right_size(False) and _is_ordered_subset(ext, name[index:]):
            replace = True
    else: # partial_type == 'replace'
        replace = True

    if replace:
        return name[:index] + ext
    return name + ext


ensure_extension.policies = (
    'none', '', 'append', '+', 'insert', '^', 'strip', '-', 'remove', 'x',
    'replace', 'r', 'create', 'c',
)


def split_extension(filename, max=None):
    """
    Upgraded version of :py:func:`os.path.splitext` that splits apart
    all the available extensions.

    Parameters
    ----------
    filename : str or ~pathlib.Path
        The file name to split.
    max : int or None, optional
        The maximum number of extensions to split off. ``max=1`` is
        equivalent to calling `os.path.splitext`. ``max=None``, zero
        or negative values means split all extensions off. Default
        is `None`.

    Returns
    -------
    parts : list
        A list containing the base name and up to `max` extensions.
        Any unsplit extensions will still be attached to the base name.
    """
    if max is None or max <= 0:
        max = -1

    parts = [filename]
    while max != 0:
        s = splitext(parts[0])
        if not s[1]:
            break
        parts[:1] = s
        max -= 1
    return parts


def insert_suffix(filename, suffix, n=0, allow_duplicate=False):
    """
    Insert a suffix into the file name before the extension.

    Append the suffix if there is no extension. By default, if the
    suffix is already present, it is not duplicated.

    Parameters
    ----------
    filename : str or ~pathlib.Path
        The name to modify.
    suffix : str
        The suffix to insert.
    n : int, optional
        The extension after which to insert the suffix. Indexing
        similar to list indexing, with ``n=0`` referring to the base
        name and ``n=-1`` the last extension. In ``"a.b.c.d"``,
        ``".d"`` is at ``n=3`` or ``n=-1``, ``"a"`` is at ``n=0`` or
        ``n=-4``. The default is to prepend to the base name: ``n=0``.
    allow_duplicate : bool
        If :py:obj:`True`, no check will be made to see if the suffix is
        already present. If :py:obj:`False` (the default), the suffix
        will only be inserted if not already present.

    Return
    ------
    inserted : str
        The modified name.
    """
    parts = split_extension(filename)
    if allow_duplicate or not parts[n].endswith(suffix):
        parts[n] += suffix
        return ''.join(parts)
    return str(filename)


class PreOpenedFile:
    """
    A proxy class for file objects that does not open or close the file
    when :py:meth:`__enter__`, :py:meth:`__exit__` and :py:meth:`close`
    are invoked.

    This version of the usual context manager is useful when processing
    opened files along with strings.

    Note that this is not a general-purpose proxy that can be used for
    most objects because it does not define any special methods besides
    :py:meth:`__repr__`, :py:meth:`__enter__`, :py:meth:`__exit__`,
    :py:meth:`__iter__` and :py:meth:`close` as class attributes.
    """
    def __init__(self, file):
        self.__file = file

    def __getattr__(self, name):
        """
        Pass through access to all missing attributes to the underlying
        file object.
        """
        return getattr(self.__file, name)

    def __repr__(self):
        """
        Return a string representation of the underlying file.
        """
        return '{}({})'.format(__class__.__name__, repr(self.__file))

    def __enter__(self, *args, **kwargs):
        """ Return this proxy object. """
        return self

    def __exit__(self, *args, **kwargs):
        """ Do nothing. """
        pass

    def __iter__(self, *args, **kwargs):
        """ Return an iterator over the underlying file. """
        return iter(self.__file)

    def close(self):
        """ Do nothing. """
        pass


def open_file(file, *args, **kwargs):
    """
    Return an open file-like object for the input.

    If the input is already a file-like object (not a string, path, or
    file descriptor), a proxy for it is returned. The original object
    remains unmodified. The proxy can be used in a context manager, but
    it will not close the file when exiting.

    Strings, paths and file descriptors are opened using the additional
    arguments provided. They return a true file object that will close
    itself when used as a context manager.

    Returns
    -------
    file : file-like
        A file-like opened from the `file` input.
    """
    # Checking for file vs descriptor
    try:
        return open(file, *args, **kwargs)
    except TypeError:
        return PreOpenedFile(file)
