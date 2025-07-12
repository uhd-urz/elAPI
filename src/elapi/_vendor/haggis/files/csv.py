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
Utilities for processing CSV files.

Among other things, this module registers a 'text' dialect with the
built-in :py:mod:`csv` module, suitable for ingesting plain text
arranged in space-separated colmns.
"""


__all__ = ['load_as_numbers', 'load_as_columns', 'reformat']


import csv, contextlib

import numpy


csv.register_dialect('text', skipinitialspace=True, delimiter=' ')


def reformat(data, format='normal'):
    """
    Convert a normal CSV dataset stored by rows into a different format.

    Valid formats are

      - ``'normal'``: Return as a list of rows.
      - ``'transpose'``: Return a list of columns.
      - ``'numpy'``: Return a numpy array.
    """
    if format not in reformat._formats:
        raise ValueError('Unsupported format {}'.format(format))
    formatter = reformat._formats[format]
    if formatter is None:
        return data
    return formatter(data)


reformat._formats = {
    'normal': None,
    'transpose': lambda data: list(map(list, zip(*data))),
    'numpy': numpy.array,
}


def load_as_numbers(file, header_lines=0, dialect='text',
                    format='normal', empty=float('nan'), **kwargs):
    """
    Load a CSV file as a numbers.

    Parameters
    ----------
    file : str or file-like
        Strings are assumed to be file names and opened. Other file-like
        objects are not closed when this function returns.
    header_lines : int
        The number of lines to skip from the beginning of the file.
    dialect : str or csv.Dialect
        The dialect to use. String options can be obtained from
        :py:func:`csv.list_dialects`.
    format : str
        One of the following data formats to use for the return value:

          - ``'normal'``: Return as a list of rows.
          - ``'transpose'``: Return a list of columns.
          - ``'numpy'``: Return a numpy array.
    empty : number
        The value to use for empty strings.
    kwargs : dict
        Any additional parameters to pass to :py:func:`csv.reader`.

    Raises
    ------
    ValueError
        If any of the elements of the file can not be converted to a
        :py:class:`float` or :py:class:`int`.
    """
    if isinstance(file, str):
        mgr = file = open(file, 'r')
    else:
        mgr = contextlib.ExitStack()

    # This is not an efficient way to load the file. Will not work well for
    # large files
    lines = []
    with mgr:
        reader = csv.reader(file, dialect, **kwargs)
        for cnt, line in enumerate(reader):
            if cnt < header_lines:
                continue
            for col, item in enumerate(line):
                line[col] = float(item) if item else empty
            lines.append(line)

    return reformat(lines, format)


def load_as_columns(file, header_lines=0, empty=float('nan'),
                    dialect='text', **kwargs):
    """
    Load a CSV file as sequence of columns rather than rows.

    Parameters
    ----------
    file : str or file-like
        Strings are assumed to be file names and opened. Other file-like
        objects are not closed when this function returns.
    header_lines : int
        The number of lines to skip from the beginning of the file.
    dialect : str or csv.Dialect
        The dialect to use. String options can be obtained from
        :py:func:`csv.list_dialects`.
    empty : number
        The value to use for missing elements. If :py:obj:`None`, the
        data may not be ragged: each line must contain the same number
        of fields as the first.
    kwargs : dict
        Any additional parameters to pass to :py:func:`csv.reader`.

    Raises
    ------
    ValueError
        If the file contains a ragged array and `empty` is set to
        :py:obj:`None`.
    """
    if isinstance(file, str):
        mgr = file = open(file, 'r')
    else:
        mgr = contextlib.ExitStack()

    # This is not an efficient way to load the file. Will not work well for
    # large files
    columns = []
    with mgr:
        reader = csv.reader(file, dialect, **kwargs)
        for cnt, line in enumerate(reader):
            if cnt < header_lines:
                continue
            elif cnt == header_lines:
                columns = [[item] for item in line]
                continue

            if len(columns) != len(line):
                if empty is None:
                    raise ValueError('Number of items in line {} '
                                     'does not match first line '
                                     '(line {})'.format(cnt, header_lines))
                if len(columns) < len(line):
                    columns.append([empty] * len(columns[0]))
                else:
                    line.append([empty] * (len(columns) - len(line)))

            for col, item in zip(columns, line):
                col.append(item)

    return columns
