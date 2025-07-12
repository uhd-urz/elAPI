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
Useful and mostly compact shortcuts for common operations.

Implementations based on some of the recipes provided in the Python
documentation, and other sources like Stack Overflow.
"""

__all__ = [
    'all_combinations', 'all_nsc', 'any_nsc', 'chained_getter',
    'CloseableMixin', 'consume', 'grouper', 'immutable', 'islast',
    'is_ordered_subset', 'KeyedSingleton', 'lenumerate', 'RangeBuilder',
    'shift_up',
]


from collections import deque
from functools import reduce
from itertools import chain, combinations, islice, repeat
from operator import index, or_, and_, attrgetter, itemgetter
import re

try:
    from contextlib import AbstractContextManager
except ImportError:
    class AbstractContextManager:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None


class CloseableMixin(AbstractContextManager):
    """
    Mixin for simple context management for objects with a
    :py:meth:`close` method.
    """

    def __exit__(self, *args):
        """
        Closes the object, returns `None`.
        """
        self.close()

    def close(self):
        """
        Default no-op implementation of `close`.

        Child classes are always expected to provide the correct
        behavior.
        """
        pass


def immutable(allow_properties=True,
              docstring='Forbids write access to class attributes.'):
    r"""
    Create a class decorator that sets a pre-defined version of
    :py:meth:`~object.__setattr__` that forbids write access to the
    attributes of a class.

    Access to properties may be allowed through `allow_properties`.
    The default setting of :py:obj:`True` does not guarantee that
    properties will be acessible, just that the parent implementation
    of :py:meth:`~object.__setattr__` will be responsible for handling
    the access.

    The messages of exceptions that are raised are based on the type of
    access that is requested. They mimic the default message that appear
    from most Python classes.

    Parameters
    ----------
    allow_properties : bool
        Whether or not to make an exception for properties. If
        :py:obj:`True`, setting of properties will be delegated to the
        parent's :py:meth:`~object.__setattr__`.
    docstring : str
        The string to associate with :py:meth:`~object.__setattr__`\ 's
        `__doc__` attibute.

    Return
    ------
    decorator : callable
        A class decorator that inserts a :py:meth:`~object.__setattr__`
        function into the decorated class.

    Notes
    -----
    Checking for properties based on the following Stack Overflow post:
    https://stackoverflow.com/a/46101204/2988730. See also the
    discussion following the answer itself.

    MRO issues with properly calling :py:meth:`~object.__setattr__` on
    properties are discussed in great detail in the answers and
    discussion surrounding https://stackoverflow.com/q/46121637/2988730.
    """
    def make_setattr(owner):
        def __setattr__(self, name, value):
            if hasattr(self, name):
                msg = 'readonly attribute'
            else:
                msg = '{!r} object has no attribute {!r}'.format(
                    type(self).__name__, name
                )
            raise AttributeError(msg)

        if allow_properties:
            default_setattr = __setattr__

            def __setattr__(self, name, value):
                typ = type(self)
                prop = getattr(typ, name, None)
                if isinstance(prop, property):
                    if owner is None:
                        return prop.__set__(self, value)
                    return super(owner, self).__setattr__(name, value)

                default_setattr(self, name, value)

        if docstring:
            __setattr__.__doc__ = docstring

        return __setattr__

    def decorator(cls):
        """
        A class decorator that assigns a special
        :py:meth:`~object.__setattr__` method to forbid attribute
        modification.
        """
        cls.__setattr__ = make_setattr(cls)
        return cls

    return decorator


def consume(iterator, n=None):
    """
    Consume an iterator entirely, or advance `n` steps ahead.

    This function is based pretty much exactly on the similarly named
    recipe in the documentation at
    https://docs.python.org/3/library/itertools.html#itertools-recipes
    """
    # Use functions that consume iterators at C speed.
    if n is None:
        # feed the entire iterator into a zero-length deque
        deque(iterator, maxlen=0)
    else:
        # advance to the empty slice starting at position n
        next(islice(iterator, n, n), None)


def grouper(iterable, n, tail=True, fillvalue=None):
    """
    Gather an iterable into chunks or blocks of fixed length.

    Based on ``grouper`` from :ref:`itertools-recipes`. The main
    difference is that this implementation allows the final chunk to
    contain fewer elements. This version also returns lazy iterables for
    the inner chunks, unlike the ``grouper`` recipe which returns
    lists.

    By default, the iterator assumes that all of the elements of a group
    have been consumed by the caller. If this is not the case, the next
    group will start with the un-consumed segment. An easy way to
    guarantee proper consumption is to use :py:func:`consume`.

    Inspired by https://stackoverflow.com/a/23926929/2988730.

    Parameters
    ----------
    iterable : iterable
        The iterable to split.
    n : int
        The size of the chunks to split into.
    tail : bool
        If :py:obj:`True`, the final group may contain fewer than `n`
        elements. If :py:obj:`False`, `fillvalue` will be used to pad
        the last group if it turns out to be shorter than `n`.
    fillvalue :
        The item to pad the final chunk with if `tail` is
        :py:obj:`False` and the iterable's length is not a multiple of
        `n`.

    Yields
    ------
    group :
        An iterable containing the next `n` or fewer elements of
        `iterable`.

    Notes
    -----
    This uses the updated generator protocol as per
    https://stackoverflow.com/a/45605358/2988730, meaning that this
    function theoretically requires Python 3.5+.
    """
    iterable = iter(iterable)
    n = index(n)
    while True:
        try:
            peek = next(iterable)
        except StopIteration:
            return
        it = iterable if tail else chain(iterable, repeat(fillvalue))
        yield chain((peek,), islice(it, n - 1))


class islast:
    """
    An iterator similar to the builtin :py:func:`enumerate`, except
    that instead of the index, it returns a boolean flag indicating if
    the current element is the last one.

    Based on the recipe at http://stackoverflow.com/a/2429118/2988730.
    Saw http://stackoverflow.com/a/2429260/2988730 after writing this.

    .. py:attribute:: last

       The last element yielded from the iteration. Available after
       the iterator is exhausted for reference. None before the
       iterator begins.
    """
    def __init__(self, iterable):
        self.last = None
        self._iter = iter(iterable)
        try:
            self._next = next(self._iter)
        except StopIteration:
            self._next = None
            self._done = True
        else:
            self._done = False

    def __iter__(self):
        return self

    def __next__(self):
        if self._done:
            raise StopIteration
        self.last = self._next
        try:
            self._next = next(self._iter)
        except StopIteration:
            self._done = True
            self._next = None
            return True, self.last
        else:
            return False, self.last


def lenumerate(iterable, seq_type=None):
    """
    A generator that returns the length of each element of `iterable` in
    addition to the element itself.

    Each element must be an iterable itself. `seq_type` controls the
    type of sequence the elements will be turned into to get the length.
    If `None`, elements are assumed to have a `len` and will not be
    altered. Otherwise, `seq_type` must be a callable that accepts one
    iterable argument and returns a valid sequence, like
    :py:class:`list`, :py:class:`tuple`, :py:class:`str` or
    :py:class:`bytearray`.

    Specifying `seq_type` is roughly equivalent to calling
    ``lenumerate(map(seq_type, iterable))``. It guarantees consumption
    of all the elements of the sub-iterables. This could be important
    for something like :py:func:`grouper`.

    The name is a portmanteau of :py:func:`len` and
    :py:func:`enumerate`.
    """
    if seq_type is None:
        seq_type = lambda x: x
    for item in iterable:
        item = seq_type(item)
        yield len(item), item


def is_ordered_subset(a, b):
    """
    Check if iterable `a` is an ordered subset of iterable `b`.

    An ordered subset means that elements can be selected from `b`
    while preserving order in such a way as to get `a`.

    For example,::

        0, 1, 2

    is an ordered subset of::

        0, 2, 1, 3, 2

    but::

        0, 3, 1

    is not.

    Source: https://stackoverflow.com/a/11820887/2988730
    """
    it = iter(b)
    return all(x in it for x in a)


def all_combinations(sequence, start=0, stop=None):
    """
    Generate all combinations of a sequence with all possible lengths.

    The smallest length is `start`, which defaults to zero. The largest
    is `stop`, which defaults to `len(sequence)`. `stop` is inclusive.

    To use an iterable with no :py:func:`len`, specify `stop` manually.

    Example::

        all_combinations([1, 2, 3])

    generates::

        (,), (1,), (2,), (3,), (1, 2), (1, 3), (2, 3), (1, 2, 3)
    """
    if stop is None:
        stop = len(sequence)
    for n in range(start, stop + 1):
        for combo in combinations(sequence, n):
            yield combo


class KeyedSingleton(type):
    """
    A meta-class for genralized singleton initialization that returns an
    existing object based on an input key.

    The key is expected to be the first argument to the class
    constructor.

    Inspired by https://stackoverflow.com/a/8665179/2988730 and
    https://stackoverflow.com/a/31723324/2988730.

    I added my own, improved answer at
    https://stackoverflow.com/a/45175660/2988730
    """
    def __init__(cls, *args, **kwargs):
        """
        Initializes the class with an empty dictionary of instances.

        Arguments are `name`, `bases`, and `attributes`, as usual.
        """
        super().__init__(*args, **kwargs)
        cls._instances = {}

    def __call__(cls, *args, **kwargs):
        """
        The constructor/initializer require at least one argument since
        the first argument is the singleton key.

        If an instance was already created with the requested key, it is
        returned without being re-allocated or re-initialized.
        """
        if not args:
            raise ValueError(
                'Instance key must be first argument in constructor'
            )
        key = args[0]
        if key in cls._instances:
            instance = cls._instances[key]
        else:
            instance = super().__call__(*args, **kwargs)
            cls._instances[key] = instance
        return instance

    def reset(cls):
        """
        Resets/clears the class's registry so that new instances will be
        constructed for further calls to `cls`.
        """
        cls._instances.clear()


def shift_up(*iterables):
    """
    For a given sequence of iterables, return a sequence of iterables
    that has all the elements shifted as far left as possible.

    In other words, earlier iterables in the sequence are replaced by
    the next available iterable as they are exhausted.

    For example, given::

        a = [1]
        b = [2, 3]
        c = [4, 5, 6]
        d = [7, 8]

    ``a, b, c, d = map(list, shift_up(a, b, c, d))`` will rearrange
    the lists so that::

        a = [1, 3, 6]
        b = [2, 5]
        c = [4, 8]
        d = [7]

    The result is a list of lists.
    """
    # Get iterators
    iterables = [iter(iterable) for iterable in iterables]
    # Generate a list of tuples containing each row
    count = len(iterables)
    shifted = [[] for _ in range(count)]
    while count > 0:
        # Generate a row
        it = 0
        while it < count:
            try:
                shifted[it].append(next(iterables[it]))
            except StopIteration:
                # Remove expired iterable
                del iterables[it]
                count -= 1
            else:
                # Keep moving along row
                it += 1

    return shifted


def any_nsc(iterable):
    """
    A non-short-circuiting version of :py:func:`any`.

    Useful for situations where the side-effects of an iterator are
    useful, for example when the elements are produced by a callable in
    a generator that also logs the :py:obj:`True` elements.

    The default behavior ``any([]) == False`` is preserved.

    See https://stackoverflow.com/q/1790520/2988730 for source material.
    """
    return reduce(or_, (bool(x) for x in iterable), False)


def all_nsc(iterable):
    """
    A non-short-circuiting version of :py:func:`all`.

    Useful for situations where the side-effects of an iterator are
    useful, for example when the elements are produced by a callable in
    a generator that also logs the :py:obj:`False` elements.

    The default behavior ``all([]) == True`` is preserved.

    See https://stackoverflow.com/q/1790520/2988730 for source material.
    """
    return reduce(and_, (bool(x) for x in iterable), True)


class RangeBuilder:
    """
    Utility for keeping tracks of the bounds of multiple ranges, e.g.,
    for the limits of a plot.

    A new builder is uninitialized at first: `start` and `stop` are
    both `None`. To add a new range, call the `update` method. The
    `start` and `stop` properties get the cumulative range.

    Any types that support mutual comparison may be supplied to
    `update`. Types that support subtraction will enable the `span`
    property as well.
    """
    def __init__(self):
        """
        Construct a new, uninitialized range builder.
        """
        self._init = False

    def __repr__(self):
        """
        Create a string representation of this object.

        The result shows the range, and is not representative of an
        actual initializer call.
        """
        args = f'{self._start}, {self._stop}' \
                                        if self._init else '<uninitialized>'
        return f'{type(self).__name__}({args})'

    @property
    def init(self):
        """
       Inidcates whether the range has been initialized or not.
        """
        return self._init

    @property
    def start(self):
        """
        The minimum lower bound of any of the ranges encountered so
        far. `None` if not initialized with at least one range.
        """
        if self._init:
            return self._start

    @property
    def stop(self):
        """
        The maximum upper bound of any of the ranges encountered so
        far. `None` if not initialized.
        """
        if self._init:
            return self._stop

    @property
    def range(self):
        """
        A list containing `[start, stop]` for a range encompassing all
        the values encountered so far.  `None` if not initialized.
        """
        if self._init:
            return [self._start, self._stop]

    @property
    def span(self):
        """
        .. py:attribute:: span

           For types that support subtraction in addition to comparison,
           This is the difference between `stop` and `start`. `None` if
           not initialized.
        """
        if self._init:
            return self._stop - self._start

    def update(self, start, stop=None):
        """
        Add a range to the builder.

        The first call to this method initializes the builder.

        Parameters
        ----------
        start :
            Any object supporting `min` comparison against the prior
            entries.
        stop :
            Any object supporting `max` comparison against the prior
            entries. Optional.
        """
        if stop is None:
            stop = start
        if self._init:
            self._start = min(start, self._start)
            self._stop = max(stop, self._stop)
        else:
            self._start = start
            self._stop = stop
            self._init = True


class chained_getter:
    r"""
    Create a getter function similar to :py:func:`operator.attrgetter`
    that can traverse a chain of index and attribute lookups.

    The `spec` string is formatted very similarly to that of
    :py:func:`operator.attrgetter`, with the addition that indices may
    be specified as well, similarly to :py:func:`operator.itemgetter`.

    Indices can be integer, positional, or named arguments. To
    specify a positional index, simply leave the brackets blank and
    supply the value in `*args`. To specify a named argument, place the
    name in brackets and add the corresponding value to `**kwargs`.

    Parameters
    ----------
    spec : str
        A format string that determines a series of attribute and index
        lookups to perform.
    \*args :
        Positional arguments to fill in for empty bracket placeholders
        in the `spec`. The index is computed from the number of empty
        brackets only.
    \*\*kwargs :
        Named arguments to fill in for brackets with key identifiers
        in `spec`.

    Return
    ------
    A callable that can look up multiple nested attributes and indices,
    similarly to, but more generally than :py:func:`operator.attrgetter`
    and :py:func:`operator.itemgetter`.

    Examples
    --------
    The following will create a getter for the first element of
    attribute ``a``::

        chained_getter('a[0]')

    Attributes may be chained::

        chained_getter('a.b[1].c.d')

    For non-numerical indices, supply the index object as a positional
    argument by leaving empty brackets. When called on object ``x``,
    the following will look up ``x.a.b['key']``::

        chained_getter('a.b[]', 'key')

    Named arguments can also be used by placing an identifier name in
    the brackets and adding the corresponding value to ``kwargs``::

        chained_getter('a.b[name]', name='key')

    Indices can be chained just like attributes, and numbers can be
    specified as any other object. Named and positional indices can be
    mixed. Position index is computed from the number of empty brackets
    found. The following will index ``[3]['key']['index'][4][5][6]``::

        chained_getter('[][name1][][][name2][name3]',
                       3, 'index', 4, name1='key', name2=5, name3=6)
    """
    _index_pattern = re.compile(r'\[([^\]]*)\]')
    _attr_pattern = re.compile(r'[\.\w]*')

    def __init__(self, spec, *args, **kwargs):
        """
        Initialize a getter for the specified parameters.
        """
        def get_index(element):
            nonlocal pos_count

            if not element:
                idx = pos_count
                pos_count += 1
                return args[idx]
            if element.replace('-', '').isdigit():
                return int(element)
            return kwargs[element]

        def get_attribute(element):
            if not self._attr_pattern.fullmatch(element):
                raise SyntaxError('Invalid characer in attribute name')
            if any(attr[0].isdigit() for attr in element.split('.') if attr):
                raise SyntaxError('Attribute name may not start with a digit')
            return element

        elements = deque()
        pos_count = 0
        for i, element in enumerate(self._index_pattern.split(spec)):
            if i % 2:
                # Handle indices
                getter = itemgetter(get_index(element))
            elif element:
                # Handle non-empty attribute chains
                if i > 0:
                    if element[0] != '.':
                        raise SyntaxError('Attribute after index '
                                          'must start with .')
                    element = element[1:]
                getter = attrgetter(get_attribute(element))
            else:
                # Skip empty attributes (separating indices)
                continue
            elements.append(getter)

        self._elements = elements

    def __call__(self, target):
        """
        Extract nested attributes from `target` object.
        """
        for getter in self._elements:
            target = getter(target)
        return target
