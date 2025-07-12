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
# Version: 27 Aug 2023: Initial Coding

"""
Tests for the :py:mod:`haggis.string_util` module.
"""


from pytest import raises

from ..string_util import (
    format_list, horiz_cat, split_horiz_cat, parse_list, parse_pair
)


class TestParsePair:
    def test_trim(self):
        parser = parse_pair(trim=str.strip)
        assert parser(' 10 -12   ') == ('10', '12')

    def test_item_type(self):
        parser = parse_pair(item_type=int)
        assert parser('10-12') == (10, 12)
        with raises(ValueError,
                    match=r"invalid literal for int\(\) with base 10: 'x'"):
            parser('x-10')

    def test_sep_multi(self):
        parser = parse_pair(sep=[':', '-'])
        assert parser('a-x') == ('a', 'x')
        assert parser('10:(d)') == ('10', '(d)')
        with raises(ValueError, match='Pair requires 2 items, found 3'):
            parser('-8:12')
        with raises(ValueError, match='Pair requires 2 items, found 1'):
            parser('10_12')

    def test_inclusive_range(self):
        parser = parse_pair.inclusive_range()
        assert parser('10-12') == range(10, 13)
        with raises(ValueError, match='Pair requires 2 items, found 3'):
            parser('-8 - 12')

    def test_inclusive_slice(self):
        parser = parse_pair.inclusive_range(sep=':', output_type=slice)
        assert parser('10:12') == slice(10, 13)
        assert parser('-8 : 4') == slice(-8, 5)


class TestParseList:
    def test_number_list(self):
        parser = parse_list.number_list()
        assert parser('1,2,4-7,8') == [1, 2, (4, 7), 8]
        assert parser('1, 3, 5, 7') == [1, 3, 5, 7]
        assert parser('2') == [2]
        assert parser('10 - 12') == [(10, 12)]
        with raises(TypeError, match=r"Unable to parse '\[10:12\]' as any of "
                r"{parse_pair\(sep='-', trim=None, item_type=int, "
                             r"output_type=None\), int}"):
            parser('[10:12]')


class TestFormatList:
    def test_empty(self):
        assert format_list([]) == ""
        assert format_list({}, width=3, format="{:0.3g}", sep="x") == ""

    def test_basic(self):
        assert format_list([1]) == "1"
        assert format_list([1, 2]) == "1, 2"
        assert format_list([1, 2, 3]) == "1, 2, 3"

    def test_sep(self):
        assert format_list([1, 2, 3], sep="x") == "1x2x3"

    def test_indent(self):
        assert format_list([1, 2, 3], indent=3) == "   1, 2, 3"
        assert format_list([1, 2, 3], indent="   ") == "   1, 2, 3"
        assert format_list([1, 2, 3], indent=[]) == "[]1, 2, 3"
        assert format_list([1, 2, 3], indent=None) == "None1, 2, 3"

    def test_width(self):
        assert format_list([1, 2, 3], width=None) == "1, 2, 3"
        assert format_list([1, 2, 3], width=1) == "1,\n2,\n3"
        raises(ValueError, format_list, [1, 2, 3], width=0)
        raises(ValueError, format_list, [1, 2, 3], width=-1)

    def test_indent_multiline(self):
        assert format_list([1, 2, 3], indent=3, width=1) == "   1,\n   2,\n   3"
        assert format_list([1, 2, 3], indent="   ", width=2) == "   1, 2,\n   3"
        assert format_list([1, 2, 3], indent=[], width=2) == "[]1, 2,\n[]3"

    def test_last_sep(self):
        assert format_list([], last_sep=" and ", width=None) == ""
        assert format_list([1], last_sep=" and ", width=None) == "1"
        assert format_list([1, 2, 3], last_sep=" and ", width=None) == "1, 2 and 3"
        assert format_list([1], last_sep=", or ", width=1) == "1"
        assert format_list([1, 2, 3], last_sep=", or ", indent=3, width=2) == "   1, 2, or\n   3"


class TestHoizCat:
    # Two equal columns
    sample_input = 'a\nabc\nab', '123\n\nx'

    # Three unequal columns
    missing_input = 'a\nabc\nxy\nz', 'b\nbc', 'c\ncde\nfg'

    def test_empty_input(self):
        assert horiz_cat(alignment='<', prefix='>', suffix='<') == ''
        with raises(IndexError, match=r'Number of headers \(1\) does not '
                                      r'match number of columns \(0\)'):
            horiz_cat(headers=['='])

    def test_empty_strings(self):
        for i in range(1, 4):
            s = [''] * i
            expected = f'>{"." * (i - 1)}<'
            assert horiz_cat(*s, sep='.',
                                   prefix='>', suffix='<') == expected

    def test_prefix(self):
        expected = '+a   123\n+abc    \n+ab  x  '
        assert horiz_cat(*self.sample_input, prefix='+') == expected

    def test_suffix(self):
        expected = 'a   123+\nabc    +\nab  x  +'
        assert horiz_cat(*self.sample_input, suffix='+') == expected

    def test_sep(self):
        expected = 'a  _123\nabc_   \nab _x  '
        assert horiz_cat(*self.sample_input, sep='_') == expected

    def test_sep_empty(self):
        expected2 = 'a  123\nabc   \nab x  '
        assert horiz_cat(*self.sample_input, sep='') == expected2

    def test_sep_not_str(self):
        with raises(AttributeError, match='\'NoneType\' object'):
            horiz_cat(*self.sample_input, sep=None)

    def test_linesep_default(self):
        expected = 'a   123\nabc    \nab  x  '
        assert horiz_cat(*self.sample_input) == expected
        assert horiz_cat(*self.sample_input, linesep='\n') == expected

    def test_linesep(self):
        expected = 'a   123-x-abc    -x-ab  x  '
        assert horiz_cat(*self.sample_input, linesep='-x-') == expected

    def test_linesep_none(self):
        expected = ['a   123', 'abc    ', 'ab  x  ']
        assert horiz_cat(*self.sample_input, linesep=None) == expected

    def test_alignment_single(self):
        for alignments, expected in [
                (('<', 'left', 'LeFt'), 'a   123\nabc    \nab  x  '),
                (('>', 'right', 'rIgHt'), '  a 123\nabc    \n ab   x'),
                (('^', 'center', 'CENTER'), ' a  123\nabc    \nab   x '),
                ((None, 'none', 'None', ''), 'a 123\nabc \nab x')]:
            for alignment in alignments:
                assert horiz_cat(*self.sample_input,
                                       alignment=alignment) == expected

    def test_alignment_multiple(self):
        for alignments, expected in [
                (['^', '>'], ' a  123\nabc    \nab    x'),
                (list('><'), '  a 123\nabc    \n ab x  ')]:
           assert horiz_cat(*self.sample_input,
                                  alignment=alignments) == expected

    def test_alignment_invalid(self):
        with raises(ValueError):
            horiz_cat(*self.sample_input, alignment='no')
        with raises(TypeError, match='object of type \'bool\''):
            horiz_cat(*self.sample_input, alignment=True)
        with raises(IndexError, match=r'Number of alignments \(0\) does not '
                                      r'match number of columns \(2\)'):
            horiz_cat(*self.sample_input, alignment=[])
        with raises(IndexError, match=r'Number of alignments \(3\) does not '
                                      r'match number of columns \(2\)'):
            horiz_cat(*self.sample_input, alignment=list('<^>'))

    def test_missing_default(self):
        expected = 'a  .b .c  \nabc.bc.cde\nxy .  .fg \nz  .  .   '
        base_expected = 'a  .123\nabc.   \nab .x  '
        assert horiz_cat(*self.missing_input, sep='.') == expected
        assert horiz_cat(*self.sample_input, sep='.') == base_expected

    def test_missing(self):
        base_expected = 'a  .123\nabc.   \nab .x  '
        for missings, expected in [
                (('empty', 'EMPTY'),
                    'a  .b .c  \nabc.bc.cde\nxy .  .fg \nz  .  .   '),
                (('down', 'DoWn'),
                    'a  .  .   \nabc.  .c  \nxy .b .cde\nz  .bc.fg '),
                (('trunc', 'tRuNc'), 'a  .b .c  \nabc.bc.cde'),
                (('last', 'Last', -1, '-1'),
                    'a  .b .c  \nabc.bc.cde\nxy .bc.fg \nz  .bc.fg '),
                (('first', 'firST', 0, '0'),
                    'a  .b .c  \nabc.bc.cde\nxy .b .fg \nz  .b .c  '),
                ((1, '1'), 'a  .b .c  \nabc.bc.cde\nxy .bc.fg \nz  .bc.cde'),
                ((-2, '-2'),
                    'a  .b .c  \nabc.bc.cde\nxy .b .fg \nz  .b .cde')]:
            for missing in missings:
                assert horiz_cat(*self.missing_input, sep='.',
                                       missing=missing) == expected
                assert horiz_cat(*self.sample_input, sep='.',
                                       missing=missing) == base_expected

    def test_missing_invalid(self):
        with raises(ValueError, match='Invalid value for `missing`: \'sdkj\''):
            horiz_cat(*self.missing_input, sep='.', missing='sdkj')
        with raises(ValueError, match=r'Invalid value for `missing`: \[\]'):
            horiz_cat(*self.missing_input, sep='.', missing=[])
        with raises(ValueError, match='Invalid value for `missing`: None'):
            horiz_cat(*self.missing_input, sep='.', missing=None)
        for m in (2, -3, '2', '-3'):
            with raises(IndexError, match='list index out of range'):
                horiz_cat(*self.missing_input, sep='.', missing=m)

    def test_len_key(self):
        expected = 'a 123\nabc \nab x'
        assert horiz_cat(*self.sample_input,
                               len_key=lambda s: 3) == expected

    def test_titles_wider_str(self):
        expected = 'col1 col2\na    123 \nabc      \nab   x   '
        assert horiz_cat(*self.sample_input,
                               titles=['col1', 'col2']) == expected

    def test_titles_with_alignment(self):
        expected = ' X    Y\n a  123\nabc    \nab    x'
        assert horiz_cat(*self.sample_input, titles=list('XY'),
                               alignment=['^', '>']) == expected

    def test_titles_scalar(self):
        expected = 'ABC ABC\na   123\nabc    \nab  x  '
        assert horiz_cat(*self.sample_input, titles='ABC') == expected

    def test_titles_empty(self):
        expected = '       \na   123\nabc    \nab  x  '
        assert horiz_cat(*self.sample_input, titles=[''] * 2) == expected

    def test_titles_multiline(self):
        expected = 'A    B  \nCDEF Z  \na    123\nabc     \nab   x  '
        assert horiz_cat(*self.sample_input,
                               titles=['A\nCDEF', 'B\nZ']) == expected

    def test_titles_diff_heights(self):
        expected = '        \nCDEF Z  \na    123\nabc     \nab   x  '
        assert horiz_cat(*self.sample_input,
                               titles=['CDEF', '\nZ']) == expected

    def test_titles_invalid(self):
        with raises(IndexError, match=r'Number of titles \(0\) does not '
                                      r'match number of columns \(2\)'):
            horiz_cat(*self.sample_input, titles=[])
        with raises(IndexError, match=r'Number of titles \(3\) does not '
                                      r'match number of columns \(2\)'):
            horiz_cat(*self.sample_input, titles=list('abc'))

    def test_headers_one_char(self):
        expected = '=   =  \na   123\nabc    \nab  x  '
        assert horiz_cat(*self.sample_input, headers='=') == expected

    def test_headers_longer_str(self):
        expected = '==== ====\na    123 \nabc      \nab   x   '
        assert horiz_cat(*self.sample_input, headers='====') == expected

    def test_headers_one_func(self):
        expected = '=== ===\na   123\nabc    \nab  x  '
        assert horiz_cat(*self.sample_input,
                               headers='='.__mul__) == expected

    def test_headers_mixed_types(self):
        expected = '==== ===\na    123\nabc     \nab   x  '
        assert horiz_cat(*self.sample_input,
                               headers=['====', '='.__mul__]) == expected

    def test_headers_longer_func(self):
        expected = '===== =====\na   123\nabc    \nab  x  '
        assert horiz_cat(*self.sample_input,
                               headers=lambda n: '=====') == expected

    def test_headers_shorter_func(self):
        expected = '== ==\na   123\nabc    \nab  x  '
        assert horiz_cat(*self.sample_input,
                               headers=lambda n: '==') == expected

    def test_headers_empty_strs(self):
        expected = '       \na   123\nabc    \nab  x  '
        assert horiz_cat(*self.sample_input,
                               headers=[''] * 2) == expected

    def test_headers_multiline(self):
        expected = '-\n- =  \na   123\nabc    \nab  x  '
        assert horiz_cat(*self.sample_input,
                               headers=['-\n-', '=']) == expected

    def test_headers_invalid(self):
        with raises(IndexError, match=r'Number of headers \(0\) does not '
                                      r'match number of columns \(2\)'):
            horiz_cat(*self.sample_input, headers=[])
        with raises(IndexError, match=r'Number of headers \(3\) does not '
                                      r'match number of columns \(2\)'):
            horiz_cat(*self.sample_input, headers=list('abc'))

    def test_hsep_default(self):
        expected = '-  +-  \na  +123\nabc+   \nab +x  '
        assert horiz_cat(*self.sample_input, headers='-',
                               sep='+') == expected

    def test_hsep(self):
        expected = 'A   B  \n-  +-  \na   123\nabc    \nab  x  '
        assert horiz_cat(*self.sample_input, headers='-',
                               titles=list('AB'), hsep='+') == expected

    def test_hsep_no_headers(self):
        expected = 'a   123\nabc    \nab  x  '
        assert horiz_cat(*self.sample_input, sep=' ',
                               hsep='xxx') == expected

    def test_hsep_one_column_headers(self):
        expected = 'a  \nabc\nab '
        assert horiz_cat(self.sample_input[0], sep=' ',
                               hsep='xxx') == expected

    def test_hsep_with_len_key(self):
        expected = '-xxx-\na 123\nabc \nab x'
        assert horiz_cat(*self.sample_input, headers='-', sep=' ',
                               hsep='xxx', len_key=lambda s: 3) == expected

    def test_hsep_invalid(self):
        with raises(ValueError,
                    match='`hsep` and `sep` must be the same length'):
            horiz_cat(*self.sample_input, headers='-', sep=' ', hsep='')
        with raises(ValueError,
                    match='`hsep` and `sep` must be the same length'):
            horiz_cat(*self.sample_input, headers='-', sep=' ',
                            hsep='xxx')
        with raises(TypeError, match='object of type \'bool\''):
            horiz_cat(*self.sample_input, headers='-', sep=' ',
                            hsep=True)
        with raises(ValueError,
                    match='`hsep` and `sep` must be the same length'):
            horiz_cat(*self.sample_input, headers='-', sep=' ',
                            hsep=[1, 'a'])
        with raises(AttributeError,
                    match='\'list\' object has no attribute \'join\''):
            horiz_cat(*self.sample_input, headers='-', sep=' ', hsep=[1])

    def test_width_greater_scalar(self):
        expected = 'a    123 \nabc      \nab   x   '
        assert horiz_cat(*self.sample_input, width=4) == expected

    def test_width_smaller_scalar(self):
        expected = 'a   123\nabc    \nab  x  '
        assert horiz_cat(*self.sample_input, width=2) == expected

    def test_width_mixed(self):
        expected = 'a   123 \nabc     \nab  x   '
        assert horiz_cat(*self.sample_input, width=[2, 4]) == expected

    def test_width_default(self):
        expected = 'a   123\nabc    \nab  x  '
        assert horiz_cat(*self.sample_input) == expected
        assert horiz_cat(*self.sample_input, width=None) == expected

    def test_width_none_mixed(self):
        expected1 = 'a   123 \nabc     \nab  x   '
        assert horiz_cat(*self.sample_input,
                               width=[None, 4]) == expected1
        expected2 = 'a    123\nabc     \nab   x  '
        assert horiz_cat(*self.sample_input,
                               width=[4, None]) == expected2

    def test_width_invalid(self):
        with raises(IndexError, match=r'Number of widths \(0\) does not '
                                      r'match number of columns \(2\)'):
            horiz_cat(*self.sample_input, width=[])
        with raises(IndexError, match=r'Number of widths \(3\) does not '
                                      r'match number of columns \(2\)'):
            horiz_cat(*self.sample_input, width=range(3))
        with raises(TypeError,
                    match='between instances of \'int\' and \'str\''):
            horiz_cat(*self.sample_input, width='xx')
        with raises(TypeError,
                    match='between instances of \'int\' and \'type\''):
            horiz_cat(*self.sample_input, width=[bool, 3])
        with raises(IndexError, match=r'Number of widths \(4\) does not '
                                      r'match number of columns \(2\)'):
            horiz_cat(*self.sample_input, width='None')

    def test_table(self):
        expected = '| Col1 |Col2 |\n|======+=====|\n|  a   | 123 |\n' \
                   '| abc  |     |\n|  ab  |  x  |'
        assert horiz_cat(*self.sample_input, prefix='|', suffix='|',
                               alignment='^', titles=['Col1', 'Col2'],
                               headers=['======', '='.__mul__], hsep='+',
                               sep='|', width=[6, 5]) == expected

class TestSplitHoizCat:
    # Two equal columns
    sample_input = ['a', 'abc', 'ab'], ['123', '', 'x']

    # Three unequal columns
    missing_input = ['a', 'abc', 'xy', 'z'], ['b', 'bc'], ['c', 'cde', 'fg']

    def test_empty_input(self):
        assert split_horiz_cat(alignment='<', prefix='>', suffix='<') == ''
        with raises(IndexError, match=r'Number of headers \(1\) does not '
                                      r'match number of columns \(0\)'):
            split_horiz_cat(headers=['='])

    def test_empty_strings(self):
        for i in range(1, 4):
            s = [['']] * i
            expected = f'>{"." * (i - 1)}<'
            assert split_horiz_cat(*s, sep='.',
                                   prefix='>', suffix='<') == expected

    def test_prefix(self):
        expected = '+a   123\n+abc    \n+ab  x  '
        assert split_horiz_cat(*self.sample_input, prefix='+') == expected

    def test_suffix(self):
        expected = 'a   123+\nabc    +\nab  x  +'
        assert split_horiz_cat(*self.sample_input, suffix='+') == expected

    def test_sep(self):
        expected = 'a  _123\nabc_   \nab _x  '
        assert split_horiz_cat(*self.sample_input, sep='_') == expected

    def test_sep_empty(self):
        expected2 = 'a  123\nabc   \nab x  '
        assert split_horiz_cat(*self.sample_input, sep='') == expected2

    def test_sep_not_str(self):
        with raises(AttributeError, match='\'NoneType\' object'):
            split_horiz_cat(*self.sample_input, sep=None)

    def test_linesep_default(self):
        expected = 'a   123\nabc    \nab  x  '
        assert split_horiz_cat(*self.sample_input) == expected
        assert split_horiz_cat(*self.sample_input, linesep='\n') == expected

    def test_linesep(self):
        expected = 'a   123-x-abc    -x-ab  x  '
        assert split_horiz_cat(*self.sample_input, linesep='-x-') == expected

    def test_linesep_none(self):
        expected = ['a   123', 'abc    ', 'ab  x  ']
        assert split_horiz_cat(*self.sample_input, linesep=None) == expected

    def test_alignment_single(self):
        for alignments, expected in [
                (('<', 'left', 'LeFt'), 'a   123\nabc    \nab  x  '),
                (('>', 'right', 'rIgHt'), '  a 123\nabc    \n ab   x'),
                (('^', 'center', 'CENTER'), ' a  123\nabc    \nab   x '),
                ((None, 'none', 'None', ''), 'a 123\nabc \nab x')]:
            for alignment in alignments:
                assert split_horiz_cat(*self.sample_input,
                                       alignment=alignment) == expected

    def test_alignment_multiple(self):
        for alignments, expected in [
                (['^', '>'], ' a  123\nabc    \nab    x'),
                (list('><'), '  a 123\nabc    \n ab x  ')]:
           assert split_horiz_cat(*self.sample_input,
                                  alignment=alignments) == expected

    def test_alignment_invalid(self):
        with raises(ValueError):
            split_horiz_cat(*self.sample_input, alignment='no')
        with raises(TypeError, match='object of type \'bool\''):
            split_horiz_cat(*self.sample_input, alignment=True)
        with raises(IndexError, match=r'Number of alignments \(0\) does not '
                                      r'match number of columns \(2\)'):
            split_horiz_cat(*self.sample_input, alignment=[])
        with raises(IndexError, match=r'Number of alignments \(3\) does not '
                                      r'match number of columns \(2\)'):
            split_horiz_cat(*self.sample_input, alignment=list('<^>'))

    def test_missing_default(self):
        expected = 'a  .b .c  \nabc.bc.cde\nxy .  .fg \nz  .  .   '
        base_expected = 'a  .123\nabc.   \nab .x  '
        assert split_horiz_cat(*self.missing_input, sep='.') == expected
        assert split_horiz_cat(*self.sample_input, sep='.') == base_expected

    def test_missing(self):
        base_expected = 'a  .123\nabc.   \nab .x  '
        for missings, expected in [
                (('empty', 'EMPTY'),
                    'a  .b .c  \nabc.bc.cde\nxy .  .fg \nz  .  .   '),
                (('down', 'DoWn'),
                    'a  .  .   \nabc.  .c  \nxy .b .cde\nz  .bc.fg '),
                (('trunc', 'tRuNc'), 'a  .b .c  \nabc.bc.cde'),
                (('last', 'Last', -1, '-1'),
                    'a  .b .c  \nabc.bc.cde\nxy .bc.fg \nz  .bc.fg '),
                (('first', 'firST', 0, '0'),
                    'a  .b .c  \nabc.bc.cde\nxy .b .fg \nz  .b .c  '),
                ((1, '1'), 'a  .b .c  \nabc.bc.cde\nxy .bc.fg \nz  .bc.cde'),
                ((-2, '-2'),
                    'a  .b .c  \nabc.bc.cde\nxy .b .fg \nz  .b .cde')]:
            for missing in missings:
                assert split_horiz_cat(*self.missing_input, sep='.',
                                       missing=missing) == expected
                assert split_horiz_cat(*self.sample_input, sep='.',
                                       missing=missing) == base_expected

    def test_missing_invalid(self):
        with raises(ValueError, match='Invalid value for `missing`: \'sdkj\''):
            split_horiz_cat(*self.missing_input, sep='.', missing='sdkj')
        with raises(ValueError, match=r'Invalid value for `missing`: \[\]'):
            split_horiz_cat(*self.missing_input, sep='.', missing=[])
        with raises(ValueError, match='Invalid value for `missing`: None'):
            split_horiz_cat(*self.missing_input, sep='.', missing=None)
        for m in (2, -3, '2', '-3'):
            with raises(IndexError, match='list index out of range'):
                split_horiz_cat(*self.missing_input, sep='.', missing=m)

    def test_len_key(self):
        expected = 'a 123\nabc \nab x'
        assert split_horiz_cat(*self.sample_input,
                               len_key=lambda s: 3) == expected

    def test_titles_wider_str(self):
        expected = 'col1 col2\na    123 \nabc      \nab   x   '
        assert split_horiz_cat(*self.sample_input,
                               titles=['col1', 'col2']) == expected

    def test_titles_with_alignment(self):
        expected = ' X    Y\n a  123\nabc    \nab    x'
        assert split_horiz_cat(*self.sample_input, titles=list('XY'),
                               alignment=['^', '>']) == expected

    def test_titles_scalar(self):
        expected = 'ABC ABC\na   123\nabc    \nab  x  '
        assert split_horiz_cat(*self.sample_input, titles='ABC') == expected

    def test_titles_empty(self):
        expected = '       \na   123\nabc    \nab  x  '
        assert split_horiz_cat(*self.sample_input, titles=[''] * 2) == expected

    def test_titles_multiline(self):
        expected = 'A    B  \nCDEF Z  \na    123\nabc     \nab   x  '
        assert split_horiz_cat(*self.sample_input,
                               titles=['A\nCDEF', 'B\nZ']) == expected

    def test_titles_diff_heights(self):
        expected = '        \nCDEF Z  \na    123\nabc     \nab   x  '
        assert split_horiz_cat(*self.sample_input,
                               titles=['CDEF', '\nZ']) == expected

    def test_titles_invalid(self):
        with raises(IndexError, match=r'Number of titles \(0\) does not '
                                      r'match number of columns \(2\)'):
            split_horiz_cat(*self.sample_input, titles=[])
        with raises(IndexError, match=r'Number of titles \(3\) does not '
                                      r'match number of columns \(2\)'):
            split_horiz_cat(*self.sample_input, titles=list('abc'))

    def test_headers_one_char(self):
        expected = '=   =  \na   123\nabc    \nab  x  '
        assert split_horiz_cat(*self.sample_input, headers='=') == expected

    def test_headers_longer_str(self):
        expected = '==== ====\na    123 \nabc      \nab   x   '
        assert split_horiz_cat(*self.sample_input, headers='====') == expected

    def test_headers_one_func(self):
        expected = '=== ===\na   123\nabc    \nab  x  '
        assert split_horiz_cat(*self.sample_input,
                               headers='='.__mul__) == expected

    def test_headers_mixed_types(self):
        expected = '==== ===\na    123\nabc     \nab   x  '
        assert split_horiz_cat(*self.sample_input,
                               headers=['====', '='.__mul__]) == expected

    def test_headers_longer_func(self):
        expected = '===== =====\na   123\nabc    \nab  x  '
        assert split_horiz_cat(*self.sample_input,
                               headers=lambda n: '=====') == expected

    def test_headers_shorter_func(self):
        expected = '== ==\na   123\nabc    \nab  x  '
        assert split_horiz_cat(*self.sample_input,
                               headers=lambda n: '==') == expected

    def test_headers_empty_strs(self):
        expected = '       \na   123\nabc    \nab  x  '
        assert split_horiz_cat(*self.sample_input,
                               headers=[''] * 2) == expected

    def test_headers_multiline(self):
        expected = '-\n- =  \na   123\nabc    \nab  x  '
        assert split_horiz_cat(*self.sample_input,
                               headers=['-\n-', '=']) == expected

    def test_headers_invalid(self):
        with raises(IndexError, match=r'Number of headers \(0\) does not '
                                      r'match number of columns \(2\)'):
            split_horiz_cat(*self.sample_input, headers=[])
        with raises(IndexError, match=r'Number of headers \(3\) does not '
                                      r'match number of columns \(2\)'):
            split_horiz_cat(*self.sample_input, headers=list('abc'))

    def test_hsep_default(self):
        expected = '-  +-  \na  +123\nabc+   \nab +x  '
        assert split_horiz_cat(*self.sample_input, headers='-',
                               sep='+') == expected

    def test_hsep(self):
        expected = 'A   B  \n-  +-  \na   123\nabc    \nab  x  '
        assert split_horiz_cat(*self.sample_input, headers='-',
                               titles=list('AB'), hsep='+') == expected

    def test_hsep_no_headers(self):
        expected = 'a   123\nabc    \nab  x  '
        assert split_horiz_cat(*self.sample_input, sep=' ',
                               hsep='xxx') == expected

    def test_hsep_one_column_headers(self):
        expected = 'a  \nabc\nab '
        assert split_horiz_cat(self.sample_input[0], sep=' ',
                               hsep='xxx') == expected

    def test_hsep_with_len_key(self):
        expected = '-xxx-\na 123\nabc \nab x'
        assert split_horiz_cat(*self.sample_input, headers='-', sep=' ',
                               hsep='xxx', len_key=lambda s: 3) == expected

    def test_hsep_invalid(self):
        with raises(ValueError,
                    match='`hsep` and `sep` must be the same length'):
            split_horiz_cat(*self.sample_input, headers='-', sep=' ', hsep='')
        with raises(ValueError,
                    match='`hsep` and `sep` must be the same length'):
            split_horiz_cat(*self.sample_input, headers='-', sep=' ',
                            hsep='xxx')
        with raises(TypeError, match='object of type \'bool\''):
            split_horiz_cat(*self.sample_input, headers='-', sep=' ',
                            hsep=True)
        with raises(ValueError,
                    match='`hsep` and `sep` must be the same length'):
            split_horiz_cat(*self.sample_input, headers='-', sep=' ',
                            hsep=[1, 'a'])
        with raises(AttributeError,
                    match='\'list\' object has no attribute \'join\''):
            split_horiz_cat(*self.sample_input, headers='-', sep=' ', hsep=[1])

    def test_width_greater_scalar(self):
        expected = 'a    123 \nabc      \nab   x   '
        assert split_horiz_cat(*self.sample_input, width=4) == expected

    def test_width_smaller_scalar(self):
        expected = 'a   123\nabc    \nab  x  '
        assert split_horiz_cat(*self.sample_input, width=2) == expected

    def test_width_mixed(self):
        expected = 'a   123 \nabc     \nab  x   '
        assert split_horiz_cat(*self.sample_input, width=[2, 4]) == expected

    def test_width_default(self):
        expected = 'a   123\nabc    \nab  x  '
        assert split_horiz_cat(*self.sample_input) == expected
        assert split_horiz_cat(*self.sample_input, width=None) == expected

    def test_width_none_mixed(self):
        expected1 = 'a   123 \nabc     \nab  x   '
        assert split_horiz_cat(*self.sample_input,
                               width=[None, 4]) == expected1
        expected2 = 'a    123\nabc     \nab   x  '
        assert split_horiz_cat(*self.sample_input,
                               width=[4, None]) == expected2

    def test_width_invalid(self):
        with raises(IndexError, match=r'Number of widths \(0\) does not '
                                      r'match number of columns \(2\)'):
            split_horiz_cat(*self.sample_input, width=[])
        with raises(IndexError, match=r'Number of widths \(3\) does not '
                                      r'match number of columns \(2\)'):
            split_horiz_cat(*self.sample_input, width=range(3))
        with raises(TypeError,
                    match='between instances of \'int\' and \'str\''):
            split_horiz_cat(*self.sample_input, width='xx')
        with raises(TypeError,
                    match='between instances of \'int\' and \'type\''):
            split_horiz_cat(*self.sample_input, width=[bool, 3])
        with raises(IndexError, match=r'Number of widths \(4\) does not '
                                      r'match number of columns \(2\)'):
            split_horiz_cat(*self.sample_input, width='None')

    def test_table(self):
        expected = '| Col1 |Col2 |\n|======+=====|\n|  a   | 123 |\n' \
                   '| abc  |     |\n|  ab  |  x  |'
        assert split_horiz_cat(*self.sample_input, prefix='|', suffix='|',
                               alignment='^', titles=['Col1', 'Col2'],
                               headers=['======', '='.__mul__], hsep='+',
                               sep='|', width=[6, 5]) == expected
