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
# Version: 03 Nov 2022: Initial Coding

"""
Tests for the :py:mod:`haggis.npy_util` module.
"""


from pytest import raises

from ..recipes import chained_getter, islast


class Namespace:
    """
    Child of object with arbitrarily assignable attributes and a
    convenience constructur.
    """
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class TestChainedGetter:
    def test_basic(self):
        spec = 'a.b[1][].c.d[key][i].e[key].f[]'
        obj = Namespace(
            a=Namespace(
                b=[None, [1, 2, Namespace(
                    c=Namespace(
                        d={'key': [Namespace(
                            e={'key': Namespace(f={'inner': 'target'})}
                        )]}
                    )
                )]]
            )
        )
        getter = chained_getter(spec, 2, 'inner', key='key', i=0)

        assert getter(obj) == 'target'

    def test_circref(self):
        obj = Namespace(a=[], b={}, z='target')
        obj.c = obj
        obj.a.append(obj)
        obj.a.append(obj.a)
        obj.a.append(obj.b)
        obj.b['obj'] = obj
        obj.b['list'] = obj.a
        obj.b['dict'] = obj.b

        assert chained_getter('c.c.c.z')(obj) == 'target'
        assert chained_getter('a[0].c.a[1][1][0].z')(obj) == 'target'
        assert chained_getter('b[].c.b[key][key][][0].z', 'obj', 'list',
                              key='dict')(obj) == 'target'

    def test_missing_arg(self):
        raises(IndexError, chained_getter, '[][]', 'a')

    def test_extra_arg(self):
        obj = {'a': {'b': 'target'}}
        assert chained_getter('[][]', *'abc')(obj) == 'target'

    def test_missing_kwarg(self):
        raises(KeyError, chained_getter, '[i][j]', i='a')

    def test_extra_kwarg(self):
        obj = {'a': {'b': 'target'}}
        assert chained_getter('[i][j]', i='a', j='b', k='c')(obj) == 'target'

    def test_extra_args(self):
        obj = {'a': {'b': 'target'}}
        assert chained_getter('[i][]', *'bc', i='a', j='b')(obj) == 'target'

    def test_bad_index(self):
        # Missing list index
        raises(IndexError, chained_getter('[]', 0), [])
        # Non-numerical list index
        raises(TypeError, chained_getter('[]', 'a'), [])
        # Missing dictionary key
        raises(KeyError, chained_getter('[]', 'a'), {})
        # Unhashable dictionary key
        raises(TypeError, chained_getter('[]', []), {})

    def test_bad_attribute(self):
        raises(AttributeError, chained_getter('a.d.c'),
               Namespace(a=Namespace(b=Namespace(c='target'))))

    def invalid_identifier(self):
        # Unterminated bracket
        raises(SyntaxError, chained_getter, 'a[')
        # Unopended bracket
        raises(SyntaxError, chained_getter, 'a]')
        # Other junk
        raises(SyntaxError, chained_getter, 'a$#%')
        # Starts with number
        raises(SyntaxError, chained_getter, '0asdf')

    def test_dots(self):
        raises(AttributeError, chained_getter('.a'), Namespace(a='target'))
        raises(AttributeError, chained_getter('.[0]'), Namespace(a=['target']))
        raises(SyntaxError, chained_getter, '[0]a')
        raises(AttributeError, chained_getter('[0].[0]'), [Namespace(a=[])])


class TestIsLast:
    def test_empty(self):
        it = islast({})
        assert it.last is None
        raises(StopIteration, next, it)

    def test_basic(self):
        numbers = [1, 2, 3]
        expected = [False, False, True]
        actual = list(islast(numbers))
        assert len(actual) == len(numbers)
        for (actual_flag, actual_num), expected_flag, expected_num in zip(actual, expected, numbers):
            assert actual_flag == expected_flag
            assert actual_num == expected_num

    def test_last(self):
        numbers = [1, 2, 3]
        it = islast(numbers)
        for _, num in it:
            assert num is it.last
        assert it.last is numbers[-1]
        raises(StopIteration, next, it)
