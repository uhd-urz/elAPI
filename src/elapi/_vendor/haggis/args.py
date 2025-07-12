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
# Version: 20 Aug 2023: Initial Coding

"""
Utilities for processing command line arguments.

This module works in conjunction with Python's standard library
:py:mod:`argparse` module.
"""


__all__ = ['SmartHelpFormatter', 'StoreVariableNargs']


from argparse import Action, ArgumentTypeError, HelpFormatter

from .string_util import format_list


class SmartHelpFormatter(HelpFormatter):
    """
    A help formatter class that can keep newlines. Currently, the
    :py:mod:`argparse` functionality can only use the default
    arguments. To change the defaults, extend this class with
    different values of the class attributes.

    Note: This class extends some private functionality in the
    API. There is no guarantee that it will work in newer versions of
    python. Please submit an issue if you experience any problems.

    .. py:attribute:: KEEP_NEWLINES

       If True, manually inserted newlines will be preserved along with
       standard line-wrapping behavior.

    .. py:attribute:: KEEP_LEADING

       If True, manually inserted leading spaces will be preserved
       while performing standard line-wrapping behavior and
       indentation.

    .. py:attribute:: TABWIDTH

       If :py:attr:`KEEP_LEADING` is True, this attribute determines
       the number of spaces by which a ``\\t`` character is replaced
       by, while preserving indentation.
    """
    KEEP_NEWLINES = True
    KEEP_LEADING = True
    TABWIDTH = 4

    def __init__(self, *args, keep_newlines=None, keep_leading=None,
                 tabwidth=None, **kwargs):
        super().__init__(*args, **kwargs)
        def check(value, default):
            return default if value is None else value
        self._keep_newlines = check(keep_newlines, self.KEEP_NEWLINES)
        self._keep_leading = check(keep_leading, self.KEEP_LEADING)
        self._tabwidth = check(tabwidth, self.TABWIDTH)

    def _get_indent(self, text):
        """
        Compute the number of leading spaces in a string. If
        ``self._keep_leading`` is False, return zero.
        """
        if self._keep_leading:
            n = len(text) - len(text.lstrip())
            n += (self._tabwidth - 1) * text[:n].count('\t')
        else:
            n = 0
        return n

    def _split_lines(self, text, width):
        """
        Overrides the behavior of the base class with the configured
        behavior for leading whitespace and newlines.
        """
        lines = text.splitlines() if self._keep_newlines else [text]
        r = []
        for line in lines:
            n = self._get_indent(line)
            r.extend(' ' * n + s
                     for s in super()._split_lines(line, width - n))
        return r

    def _fill_text(self, text, width, indent):
        """
        Overrides the behavior of the base class with the configured
        behavior for leading whitespace and newlines.
        """
        lines = text.splitlines() if self._keep_newlines else [text]
        r = []
        for line in lines:
            n = self._get_indent(line)
            r.append(super()._fill_text(line, width, indent + n * ' '))
        return '\n'.join(r)


class StoreVariableNargs(Action):
    """
    Replacement for action='store' when `nargs` can be a range or a
    discrete set.

    Instead of using integer `nargs`, provide a :py:class:`set`,
    :py:class:`range`, or other container of integers for `nargs`::

        parser.add_argument('-a', action=StoreVariableNargs, nargs={1, 3})

    `nargs` defaults to ``range(1, 2)``.

    Internally, `nargs` will be represented as `'*'` so the action can
    have a standard string representation.
    """
    def __init__(self, nargs=range(1, 2), **kwargs):
        super().__init__(**kwargs)
        self.nargs = '*'
        self.arg_spec = nargs

    def __call__(self, parser, args, values, option_string=None):
        if len(values) not in self.arg_spec:
            raise ArgumentTypeError(
                'argument {}: expected {} arguments'.format(
                    option_string,
                    format_list(self.arg_spec, last_sep=", or ", width=None)
                )
            )
        setattr(args, self.dest, values)
