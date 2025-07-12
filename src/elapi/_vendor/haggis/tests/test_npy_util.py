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
# Version: 01 Jun 2022: Initial Coding

"""
Tests for the :py:mod:`haggis.npy_util` module.
"""


import numpy as np
from pytest import raises

from ..npy_util import find_peaks, masked_index, replace_field, unmasked_index


class TestReplaceField:
    inner = np.dtype([('Roll', np.float32),
                      ('Pitch', np.float32),
                      ('Yaw', np.float32)])
    inner2 = np.dtype([('RollPitchYaw', np.float32, 3)])
    outer = np.dtype([('Position', np.float32, 3),
                      ('Attitude', inner)])
    outer2 = np.dtype([('Position', np.float32, 3),
                       ('Attitude', np.float32, 3)])

    def test_replace_custom(self):
        result = replace_field(self.outer, np.float32, 'Attitude')
        expected = self.outer2
        assert result == expected

    def test_replace_with_custom(self):
        result = replace_field(self.outer2, self.inner, 'Attitude')
        assert result == self.outer

    def test_empty_fields(self):
        result = replace_field(self.inner, np.float32)
        expected = self.inner2
        assert result == expected

    def test_name(self):
        dt = np.dtype([('snake', np.float32),
                       ('toSnake', np.float32),
                       ('toCamel', np.float32),
                       ('ToCAMEL', np.float32),
                       ('X', np.float32)])

        result = replace_field(dt, np.float32, name='RPY')
        expected = np.dtype([('RPY', np.float32, 5)])
        assert result == expected

        expected = np.dtype([('snake_toSnake_toCamelToCAMEL_X', np.float32, 5)])
        result = replace_field(dt, np.float32)

    def test_order(self):
        result = replace_field(self.inner, np.float32, 'Roll', 'Pitch', 'Yaw')
        expected = np.dtype([('RollPitchYaw', np.float32, 3)])
        assert result == expected

        result = replace_field(self.inner, np.float32, 'Yaw', 'Pitch', 'Roll')
        expected = np.dtype([('YawPitchRoll', np.float32, 3)])
        assert result == expected

    def test_nested(self):
        result = replace_field(
            self.outer, replace_field(self.inner, np.float32), 'Attitude'
        )
        expected = np.dtype([
            ('Position', np.float32, 3), ('Attitude', self.inner2)
        ])
        assert result == expected

    def test_span(self):
        result = replace_field(self.inner, np.float64, 'Yaw', 'Pitch')
        expected = np.dtype([('Roll', np.float32),
                             ('YawPitch', np.float64)])
        assert result == expected

        raises(ValueError, replace_field, self.inner, np.float64, 'Yaw', 'Roll')

    def test_align(self):
        spec = [('a', np.int32), ('b', np.int8), ('c', np.int32)]
        dt = np.dtype(spec, align=True)

        result = replace_field(dt, np.int8, 'b')
        expected = dt
        assert result == expected

        result = replace_field(dt, np.int8, 'b', 'c')
        expected = np.dtype([('a', np.int32), ('b_c', np.int8, 8)])
        assert result == expected

        dt = np.dtype(spec, align=False)

        result = replace_field(dt, np.int8, 'b')
        expected = dt
        assert result == expected

        result = replace_field(dt, np.int8, 'b', 'c')
        expected = np.dtype([('a', np.int32), ('b_c', np.int8, 5)])
        assert result == expected

    def test_union(self):
        result = replace_field(self.inner, np.float32, 'Yaw', 'Roll')
        expected = np.dtype({
            'names': ['YawRoll', 'Pitch'],
            'formats': [(np.float32, 3), np.float32],
            'offsets': [0, 4],
            'itemsize': 12,
        })
        assert result == expected

    def test_nofields(self):
        raises(ValueError, replace_field, np.dtype(np.float32), np.float32)

    def test_missing(self):
        raises(ValueError, replace_field, self.inner, np.float32, 'XXX')


class TestUnmaskedIndex:
    def test_empty_array(self):
        assert (unmasked_index((), []) == []).all()
        assert (unmasked_index([], []) == []).all()
        raises(IndexError, unmasked_index, 0, [])

    def test_empty_mask(self):
        raises(IndexError, unmasked_index, 0, [False, False, False])

    def test_bad_type(self):
        raises(IndexError, unmasked_index, [1.0, 2.0], np.ones(5, bool))

    def test_non_bool(self):
        expected = [1, 3]
        mask = [1.0, 2.0, 0.0, 3.0]
        result = unmasked_index([1, 2], mask)
        assert (result == expected).all()

    def test_out_of_bounds(self):
        raises(IndexError, unmasked_index, 2, [True, True, False])
        raises(IndexError, unmasked_index, -3, [True, True, False])

    def test_tuple(self):
        expected = [4, 3]
        result = unmasked_index((3, 2), [True, True, False, True, True])
        assert (result == expected).all()

    def test_f_order(self):
        expected = ([0, 1], [1, 2])
        index = [1, 2]
        mask = np.array([[True, True, False], [False, False, True]], order='F')

        result = unmasked_index(index, mask)

        assert len(result) == 2
        for r, e in zip(result, expected):
            assert (r == e).all()

    def test_simple(self):
        expected = [4, 0, 1, 7]
        index = [2, 0, 1, 3]
        mask = [True, True, False, False, True, False, False, True]
        result = unmasked_index(index, mask)
        assert (result == expected).all()

    def test_ndarray(self):
        expected = ([[2, 0], [1, 0]], [[2, 1], [3, 0]])
        index = [[4, 1], [3, 0]]
        mask = [[True, True, False, False],
                [True, False, False, True],
                [False, False, True, False]]
        result = unmasked_index(index, mask)
        assert len(result) == 2
        for r, e in zip(result, expected):
            print(r, e, sep='\n')
            assert (r == e).all()

    def test_negative(self):
        expected = ([[2, 0], [1, 0]], [[2, 1], [3, 0]])
        index = [[-1, -4], [-2, -5]]
        mask = [[True, True, False, False],
                [True, False, False, True],
                [False, False, True, False]]
        result = unmasked_index(index, mask)
        assert len(result) == 2
        for r, e in zip(result, expected):
            assert (r == e).all()


class TestMaskedIndex:
    def test_out_of_bounds(self):
        raises(IndexError, masked_index, 0, [])
        raises(IndexError, masked_index, -3, [True, False])
        raises(IndexError, masked_index, 2, [True, False])
        raises(IndexError, masked_index, (-1, 2), [[True, False]])
        raises(IndexError, masked_index, (1, 0), [[True, False]])

    def test_wrong_dims(self):
        raises(ValueError, masked_index, 0, [[True]])
        raises(ValueError, masked_index, (0, 0, 0), [[True]])

    def test_promotion(self):
        result = masked_index(0, False)
        assert result == -1

        raises(IndexError, masked_index, 1, False)

    def test_not_bool(self):
        result = masked_index(0, [1, 2])
        assert result == 0

    def test_unmasked_portion(self):
        result = masked_index((), False)
        assert result == -1

        result = masked_index(0, [False, True])
        assert result == -1

        result = masked_index((1, 1), [[True, True], [True, False]])
        assert result == -1

    def test_simple(self):
        expected = [0, 2, 3]
        index = [1, 3, 4]
        mask = [False, True, True, True, True, False]
        result = masked_index(index, mask)
        assert (result == expected).all()

    def test_ndarray(self):
        expected = [[0, 8, 1, 2], [9, 11, 3, 7]]
        index = (
            [[0, 1, -2, 0], [-1, 1, -2, -1]],
            [[0, -2, -3, 1], [-2, 2, 1, 0]],
            [[0, -4, 1, -3], [2, -2, 3, -1]]
        )
        mask = [
            [[True, True, False, False],
             [False, True, False, True],
             [False, False, True, True]],
            [[True, False, False, True],
             [True, False, True, False],
             [False, True, True, False]]
        ]
        result = masked_index(index, mask)
        assert (result == expected).all()

    def test_negative(self):
        expected = [0, -1]
        index = ([1, 0], [0, 0])
        mask = [[False], [True]]
        result = masked_index(index, mask)
        assert (result == expected).all()

    def test_broadcast(self):
        expected = [
            [[[0, -1, 1], [0, -1, 1]],
             [[-1, 2, 3], [-1, 2, 3]],
             [[0, -1, 1], [0, -1, 1]]],
            [[[-1, 2, 3], [-1, 2, 3]],
             [[0, -1, 1], [0, -1, 1]],
             [[-1, 2, 3], [-1, 2, 3]]]
        ]
        index = (
            [[[[0]], [[1]], [[0]]], [[[1]], [[0]], [[1]]]],
            [[0, 1, 2], [0, 1, 2]]
        )
        mask = [[True, False, True], [False, True, True]]
        result = masked_index(index, mask)
        assert result.shape == (2, 3, 2, 3)
        assert (result == expected).all(None)


class TestFindPeaks:
    def test_empty(self):
        result = find_peaks([])
        assert (result == []).all()

    def test_single(self):
        result = find_peaks([1.0])
        assert (result == [0]).all()

    def test_flat(self):
        result = find_peaks([0, 1, 1, 1, 1, 1, 0, 2, 2, 2, 2, 3, 3, 3, 3, 3])
        assert (result == [11, 1]).all()

    def test_order_n(self):
        result = find_peaks([0, 2, 1, 3], n_peaks=1)
        assert (result == [3]).all()

        result = find_peaks([0, 2, 1, 3], n_peaks=5)
        assert (result == [3, 1]).all()

    def test_dates(self):
        expected_ind = [3, 5]
        expected_val = np.array(['2022-10-14 10:00:00', '2022-10-14 00:00:00'],
                                dtype='datetime64[ns]')
        dates = np.array([
            '2022-10-13 10:00:00', '2022-10-13 10:30:00',
            '2022-10-13 11:00:00', '2022-10-14 10:00:00',
            '2022-10-13 23:00:00', '2022-10-14 00:00:00'],
            dtype='datetime64[ns]')
        ind, val = find_peaks(dates, mode='value', return_values=True)
        print(ind, expected_ind, sep='\n')
        assert (ind == expected_ind).all()
        assert val.dtype == dates.dtype
        assert (val == expected_val).all()

        ind, val = find_peaks(dates, mode='index', return_values=True)
        assert (ind == expected_ind).all()
        assert val.dtype == dates.dtype
        assert (val == expected_val).all()

    def test_obj(self):
        data = np.empty(5, dtype=object)
        data[0] = []
        data[1] = set()
        data[2] = np.zeros(3)
        data[3] = {}
        data[4] = '1'
        raises(TypeError, find_peaks, data)

    def test_mode(self):
        data = [1, 1, 0, 2, 4, 4, 4, 0, 3, 5]

        raises(ValueError, find_peaks, data, mode='invalid')
        raises(TypeError, find_peaks, data, mode=None)
        raises(TypeError, find_peaks, data, mode=b'value')

        expected = [9, 4, 0]
        result = find_peaks(data, n_peaks=2, mode='value')
        assert (result == expected[:2]).all()
        result = find_peaks(data, mode='vAluE')
        assert (result == expected).all()

        expected = [0, 4, 9]
        result = find_peaks(data, n_peaks=2, mode='index')
        assert (result == expected[:2]).all()
        result = find_peaks(data, mode='INdeX')
        assert (result == expected).all()

    def test_ravel(self):
        data = [[0, 0, 0, 1], [1, 2, 3, 2], [1, 0, 0, 0]]
        expected = [6]
        result = find_peaks(data)
        assert (result == expected).all()

    def test_return_values(self):
        result = find_peaks([0, 3, 0, 1], 2, return_values=True)
        assert len(result) == 2

        ind, val = result
        assert (ind == [1, 3]).all()
        assert (val == [3, 1]).all()

    def test_npeaks(self):
        data = [2, 0, 1, 3, 2, 4, 10, 8, 5, 6, 5, 4, 5]

        expected = [6, 9, 12, 3, 0]
        result = find_peaks(data, mode='value')
        print(result)
        print(expected)
        assert (result == expected).all()
        result = find_peaks(data, 2, mode='value')
        assert (result == expected[:2]).all()

        expected = [0, 3, 6, 9, 12]
        result = find_peaks(data, mode='index')
        assert (result == expected).all()
        result = find_peaks(data, 3, mode='index')
        assert (result == expected[:3]).all()
