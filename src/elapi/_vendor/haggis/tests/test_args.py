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
# Version: 27 Jan 2022: Initial Coding

"""
Tests for the :py:mod:`haggis.args` module.
"""


from argparse import ArgumentParser, ArgumentTypeError

from pytest import raises

from ..args import SmartHelpFormatter, StoreVariableNargs


class TestSmartHelpFormatter:
    def test_get_indent(self):
        class NoLeading(SmartHelpFormatter):
            KEEP_LEADING = False
        fmt = NoLeading('', 2, 24, 80)
        assert fmt._get_indent('x') == 0
        assert fmt._get_indent('    x') == 0
        assert fmt._get_indent(' \t  x') == 0
        assert fmt._get_indent(' \t  x\t\t') == 0

        fmt = SmartHelpFormatter('', 2, 24, 80)
        assert fmt._get_indent('x') == 0
        assert fmt._get_indent('    x') == 4
        assert fmt._get_indent(' \t  x') == 7
        assert fmt._get_indent(' \t  x\t\t') == 7

    def test_split_lines(self):
        class NoNewlines(SmartHelpFormatter):
            KEEP_NEWLINES = False
        fmt = NoNewlines('', 2, 24, 80)
        assert fmt._split_lines('x', 80) == ['x']
        assert fmt._split_lines('    x', 80) == ['    x']
        assert fmt._split_lines(' \t  x', 80) == ['       x']
        assert fmt._split_lines('x\n', 80) == ['x']
        assert fmt._split_lines('    x\ny', 80) == ['    x y']
        assert fmt._split_lines(' \t  x\ny\n      zzz zzz', 10) == ['       x y', '       zzz', '       zzz']

        fmt = SmartHelpFormatter('', 2, 24, 80)
        assert fmt._split_lines('x', 80) == ['x']
        assert fmt._split_lines('    x', 80) == ['    x']
        assert fmt._split_lines(' \t  x', 80) == ['       x']
        assert fmt._split_lines('x\n', 80) == ['x']
        assert fmt._split_lines('    x\ny', 80) == ['    x', 'y']
        assert fmt._split_lines(' \t  x\ny\n      zzz zzz', 10) == ['       x', 'y', '      zzz', '      zzz']

    def test_fill_text(self):
        class NoNewlines(SmartHelpFormatter):
            KEEP_NEWLINES = False
        fmt = NoNewlines('', 2, 24, 80)
        assert fmt._fill_text('x', 80, '  ') == '  x'
        assert fmt._fill_text('    x', 80, '  ') == '      x'
        assert fmt._fill_text(' \t  x', 80, '  ') == '         x'
        assert fmt._fill_text('x\n', 80, '  ') == '  x'
        assert fmt._fill_text('    x\ny', 80, '  ') == '      x y'
        assert fmt._fill_text(' \t  x\ny\n      zzz zzz', 12, '  ') == '         x y\n         zzz\n         zzz'

        fmt = SmartHelpFormatter('', 2, 24, 80)
        assert fmt._fill_text('x', 80, '  ') == '  x'
        assert fmt._fill_text('    x', 80, '  ') == '      x'
        assert fmt._fill_text(' \t  x', 80, '  ') == '         x'
        assert fmt._fill_text('x\n', 80, '  ') == '  x'
        assert fmt._fill_text('    x\ny', 80, '  ') == '      x\n  y'
        assert fmt._fill_text(' \t  x\ny\n      zzz zzz', 12, '  ') == '         x\n  y\n        zzz\n        zzz'


class TestStoreVariableNargs:
    def test_default(self):
        parser = ArgumentParser()
        action = parser.add_argument("-a", action=StoreVariableNargs)
        assert action.nargs == '*'
        assert parser.parse_args([]).a is None
        assert parser.parse_args(['-a', 'X']).a == ['X']
        raises(ArgumentTypeError, parser.parse_args, ['-a'])
        raises(ArgumentTypeError, parser.parse_args, ['-a', 'X', 'Y'])

    def test_set(self):
        parser = ArgumentParser()
        action = parser.add_argument("-a", action=StoreVariableNargs, nargs={1, 3})
        assert action.nargs == '*'
        assert parser.parse_args([]).a is None
        assert parser.parse_args(['-a', 'X']).a == ['X']
        assert parser.parse_args(['-a', 'X', 'Y', 'Z']).a == ['X', 'Y', 'Z']
        raises(ArgumentTypeError, parser.parse_args, ['-a'])
        raises(ArgumentTypeError, parser.parse_args, ['-a', 'X', 'Y'])
        raises(ArgumentTypeError, parser.parse_args, ['-a', 'W', 'X', 'Y', 'Z'])

    def test_range(self):
        parser = ArgumentParser()
        action = parser.add_argument("-a", action=StoreVariableNargs, nargs=range(3))
        assert action.nargs == '*'
        assert parser.parse_args([]).a is None
        assert parser.parse_args(['-a']).a == []
        assert parser.parse_args(['-a', 'X']).a == ['X']
        assert parser.parse_args(['-a', 'X', 'Y']).a == ['X', 'Y']
        raises(ArgumentTypeError, parser.parse_args, ['-a', 'X', 'Y', 'Z'])
