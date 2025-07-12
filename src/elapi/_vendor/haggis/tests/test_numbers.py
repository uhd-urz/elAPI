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
# Version: 22 Jan 2022: Initial Coding

"""
Tests for the :py:mod:`haggis.numbers` module.
"""


from pytest import raises

from ..numbers import as_base, digit_count


class TestAsBase:
    def test_stack_overflow(self):
        """
        Test from https://stackoverflow.com/a/28666223/2988730, also
        shows that `letters` gets ignored.
        """
        n = 67854 ** 15 - 102
        base = 577
        expected = [4, 473, 131, 96, 431, 285, 524, 486, 28, 23,
                    16, 82, 292, 538, 149, 25, 41, 483, 100, 517,
                    131, 28, 0, 435, 197, 264, 455]
        assert as_base(n, base, letters=True) == expected

    def test_negative(self):
        n = -100
        base = 3
        expected_string = '-10201'
        expected_list = [1, 0, 2, 0, 1]
        assert as_base(n, base, letters=True) == expected_string
        assert as_base(n, base, letters=False) == expected_list

    def test_one(self):
        n = 10
        base = 1
        expected = '1111111111'
        assert as_base(n, base, letters=True) == expected

    def test_non_int(self):
        raises(TypeError, as_base, 0.1)
        raises(ValueError, as_base, 'a')

    def test_negative_base(self):
        raises(ValueError, as_base, 10, -12)


class TestDigitCount:
    def test_one(self):
        n = 100
        assert digit_count(n, 1) == n

    def test_dec(self):
        n = 12877617349487594742394872304230
        assert digit_count(n, 10) == 32

    def test_bin(self):
        n = 0b1010101001000010010011101101
        assert digit_count(n, 2) == 28

    def test_dec(self):
        n = 0o561761237213572357
        assert digit_count(n, 8) == 18

    def test_dec(self):
        n = 12877617349487594742394872304230
        assert digit_count(n, 10) == 32

    def test_hex(self):
        n = 0x12389BE98489F2377BE23ECBD1AEAD3578DB
        assert digit_count(n, 16) == 36

    def test_large(self):
        n = 10**1000
        assert digit_count(n, 10) == 1000

    def test_invalid(self):
        raises(TypeError, digit_count, 8.1)
        raises(TypeError, digit_count, 100, base=7.5)
