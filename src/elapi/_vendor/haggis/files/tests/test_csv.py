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
# Version: 11 Jan 2022: Initial Coding

"""
Tests for the :py:mod:`haggis.files.csv` module.
"""


import numpy
from pytest import raises

from ..csv import reformat


class TestReformat:
    def setup_method(self):
        self.data = [[1, 'a'], [2, 'b'], [3, 'c']]

    def test_normal(self):
        assert reformat(self.data, 'normal') is self.data

    def test_transpose(self):
        assert reformat(self.data, 'transpose') == [[1, 2, 3], ['a', 'b', 'c']]

    def test_numpy(self):
        result = reformat(self.data, 'numpy')
        assert isinstance(result, numpy.ndarray)
        assert result.shape == (len(self.data), len(self.data[0]))
        numpy.testing.assert_array_equal(result, numpy.array(self.data))

    def test_invalid(self):
        with raises(ValueError):
            reformat(self.data, 'invalid')
