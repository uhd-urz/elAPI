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
# Version: 09 Jan 2021: Initial Coding

"""
Recipes specifically for manipulating and emulating mappings, namespaces
and the like.

Implementations based on some of the recipes provided in the Python
documentation, and other sources like Stack Overflow.
"""

__all__ = [
    'dict_merge', 'dict_select', 'mapping_context', 'Namespace',
    'option_lookup', 'RecursiveDict', 'setdefaults',
]


from collections.abc import Mapping
from itertools import starmap
from warnings import warn

from .exceptions import ErrorTransform
from .recipes import consume


def dict_select(dic, keys=None, exclude=None, extra='ignore'):
    """
    Filter a dictionary so only the specified keys are present.

    Parameters
    ----------
    dic : dict
        The dictionarty to filter.
    keys : iterable or None
        The keys to include in the output. Another dictionary may be
        used since it iterates over its keys by default. :py:obj:`None`
        means to use all keys.
    exclude : container or None
        The keys to exclude. Anything that supports the `in` operator is
        valid here. `exclude` takes precedence over `keys`: no keys in
        `exclude` will be present in the output, even if they are
        present in `keys`.
    extra : {'ignore', 'err', 'warn'}
        How to handle members of `dic` that are neither in `keys` nor
        explicitly listed in `exclude`:

        ignore :
            Skip over extra keys.
        err :
            Issue an error if invalid keys are found.
        warn :
            Issue a warning if extra keys are found.

        Values other than `'ignore'` will compare sets of keys.

    Return
    ------
    selection : dict
        A new `dict` object, even if `keys` is a superset of the actual
        keys found in `dic`.

    Notes
    -----
    The default behavior is just to make a copy of `dic`.
    """
    input_keys = set(dic.keys())
    select_keys = input_keys if keys is None else set(keys)
    exclude_keys = set() if exclude is None else set(exclude)

    if extra != 'ignore':
        extra_keys = (input_keys - select_keys) - exclude_keys
        extra_fmt = ', '.join(str(k) for k in extra_keys)
        message = 'Found extra keys: {}'.format(extra_fmt)
        if extra == 'warn':
            warn(message)
        elif extra == 'err':
            raise KeyError(message)
        else:
            raise ValueError('Invalid value of `extra`: "{}"'.format(extra))

    selection = (input_keys & select_keys) - exclude_keys

    return {k: dic[k] for k in selection}


def dict_merge(parent, child, keys=None, exclude=None, key=None):
    """
    Filter a parent dictionary and override it with values from a
    child, if supplied as a mapping.

    Parameters
    ----------
    parent : dict
        The base mapping to get the keys from.
    child : dict, value or None
        If a mapping type, `child[key]` will be the main value and the
        remaining keys will override the values obtained from `parent`.
        Otherwise, `child` will be the main value. If :py:obj:`None`,
        treated as missing entirely.
    keys : iterable or None
        An iterable of the keys to extract from `parent` and `child`, if
        it is a mapping. Should not contain `key`. :py:obj:`None` means
        to use all the keys of `parent`.
    exclude : container or None
        Keys to omit from the final result, even if they are present in
        `keys`.
    key :
        The name of the main value in `parent`, if it is not overriden
        by `child`. If `child` is a mapping, either it or `parent` must
        contain this key. Otherwise, the value of child is the value of
        the key.

    Return
    ------
    main: value (opt)
        The value of the main key, only returned if `key` is not
        :py:obj:`None`. If `child` is a mapping type, either it or
        `parent` will provide the key. Otherwise, it will be `child`
        itself.
    selection:
        The selected values of `parent`, possibly overriden by `child`
        if it is a mapping.
    """
    selection = dict_select(parent, keys, exclude)
    cmap = isinstance(child, Mapping)

    if cmap:
        selection.update(dict_select(child, keys, exclude))

    if key is None:
        return selection

    if child is None:
        value = parent[key]
    elif cmap:
        value = child[key] if key in child else parent[key]
    else:
        value = child

    return value, selection


def setdefaults(mapping, *args, **kwargs):
    """
    Update missing keys in this mapping based on supplied iterables and
    mappings.

    This is similar to :py:meth:`dict.update`, except that only missing
    keys are added.

    Parameters
    ----------
    mapping :
        The dictionary to update. If the type does not have a
        `setdefault` method, the udpate will default to using
        `__contains__` and `__setitem__` directly.
    *args :
        Each positional arguments may be a mapping or an iterable of
        two-element iterables. Iterables are applied in order. Only the
        first instance of a duplicated key is ever considered.
    **kwargs :
        Any additional keywords to insert. These are applied after the
        iterables, if any.
    """
    # Find suitable setdefault implementation
    if hasattr(mapping, 'setdefault') and callable(mapping.setdefault):
        func = mapping.setdefault
    else:
        def func(key, default):
            if not key in mapping:
                ret = mapping[key] = default
            else:
                ret = mapping[key]
            # For correctness
            return ret

    for arg in args:
        if isinstance(arg, Mapping):
            arg = arg.items()
        consume(starmap(func, arg))
    consume(starmap(func, kwargs.items()))


class RecursiveDict(dict):
    """
    Mapping that allows recursive lookup of keys.

    Lookup can be controlled by specifying a key type and/or a value
    type. A value suitable for recursion that is not found as a key
    raises a :py:exc:`KeyError`, while a value of the wrong type raises
    a :py:exc:`TypeError`. Requesting a key of the wrong type raises a
    :py:exc:`TypeError` as well.

    Only lookup operations are different from :py:class:`dict`\ :
    :py:meth:`__getitem__`, :py:meth:`setdefault` and :py:meth:`get`.
    :py:meth:`~dict.pop` and :py:meth:`~dict.popitem` are not modified.
    Full control is provided through the unaltered setter operations.

    Here is an example of how :py:attr:`value_type` affects the lookup::

        d = RecursiveDict({'a': 1, 'b': 'a'})
        print(d.setdefault('d', 'c'))  # Prints "c"

    vs::

        d = RecursiveDict({'a': 1, 'b': 'a'}, value_type=int)
        print(d.setdefault('d', 'c'))  # Raises "KeyError: 'c'"

    .. py:attribute:: key_type

       A class object indicating the type that may be used as a key.
       :py:obj:`None` indicates "any". The default is :py:class:`str`.
       Values of this type indicate recursive lookup.

    .. py:attribute:: value_type

       A class object indicating the type that may be used as a value.
       :py:obj:`None`, the default, indicates "any" type.
    """
    __slots__ = ('key_type', 'value_type')

    def __init__(self, *args, key_type=str, value_type=None, **kwargs):
        """
        Construct a new mapping with the specified key and value types.

        All normal :py:class:`dict` constructor arguments are accepted.

        `key_type` and `value_type` may be classes, tuples of classes,
        or :py:obj:`None`. The latter case is equivalent to "anything
        goes". The dictionary will accept keys and values of the wrong
        type, but will raise an error on lookup, so it is best to leave
        either `key_type` or `value_type` as :py:obj:`None`.

        If both types are constrained and there is overlap between them,
        `key_type` always takes precedence: a value that can be a
        `key_type` is always looked up as a key. Only when the lookup
        fails is the value returned.

        If `key_type` is constrained, but `value_type` is not, lookup
        continues until a :py:exc:`KeyError` is raised or a
        non-\ `key_type` value is encountered. Similarly, if only
        `value_type` is constrained, lookup continues until a
        :py:exc:`KeyError` is raised or a value of the requested type
        is found.

        There is no constraint on either (both are `None`), recursion
        will stop only when a value is not present in the dictionary as
        a key.
        """
        self.key_type = key_type
        self.value_type = value_type
        super().__init__(*args, **kwargs)

    def __getitem__(self, key):
        """
        Recursively fetch an item from this dictionary.
        """
        return self._conditional_get(key, iskey=True)[1]

    def setdefault(self, key, default=None):
        """
        Set the key to the specified value if not found, return the
        value for the key.

        The default value is set exactly as specified, but the return
        value is dereferenced.
        """
        if key in self:
            return self[key]
        self[key] = default
        return self._conditional_get(default)[1]

    def get(self, key, default=None):
        """
        Retrieve a fully dereferenced value for `key` if present, or
        `default` if not.

        `default` gets dereferenced if the key is not present.
        """
        if key in self:
            return self[key]
        return self._conditional_get(default)[1]

    def final_key(self, key):
        """
        In a recursive reference, retreive the final key that actually
        contains the value mapping.

        For example, given::

            x = RecursiveDict(key_type=str, value_type=int)
            x['a'] = 'b'
            x['b'] = 'c'
            x['c'] = 1

        The result of :py:meth:`final_key` on any of the keys defined
        above would be ``'c'``.

        If the final key does not contain a value, it will still be
        returned. This means that if the dictionary above were to have
        ``x['c'] = 'd'`` (a broken recursion), :py:meth:`final_key`
        would return ``'c'`` regardless.

        Passing in a missing key will raise a :py:exc:`KeyError` as
        usual.
        """
        return self._conditional_get(key, iskey=True, err=False)[0]

    def _conditional_get(self, obj, iskey=False, err=True):
        """
        Check if the object is a possible key, and correctly retrieve
        the dereferenced value for it.

        If the value is a key type, but is not a valid key, it must also
        be a valid value type to avoid raising a :py:exc:`KeyError`.

        Parameters
        ----------
        obj :
            The object to search for.
        iskey : bool
            :py:obj:`True` if `obj` is required to be a key on the
            first iteration. Otherwise it represents a value (which may
            be a recursive key).
        err : bool
            Whether or not to raise an error if the key is not found.
        """
        key = obj if iskey else None
        while self._check_key_or_value_type(obj, iskey=iskey):
            try:
                new = super().__getitem__(obj)
            except KeyError:
                if err and (iskey or
                            not self._check_value_type(obj, err=False)):
                    raise
                break
            else:
                key = obj
                obj = new
            iskey = False
        return key, obj

    def _check_key_type(self, key, err=True):
        """
        Verify that the selected object is a valid key.

        Return the status, or raise a :py:exc:`TypeError` if `err` is
        :py:obj:`True`.
        """
        if self.key_type is None or isinstance(key, self.key_type):
            return True
        if err:
            raise TypeError('{} not allowed for keys'.format(type(key)))
        return False

    def _check_value_type(self, value, err=True):
        """
        Verify that the selected object is a valid value.

        Return the status, or raise a :py:exc:`TypeError` if `err` is
        :py:obj:`True`.
        """
        if self.value_type is None or isinstance(value, self.value_type):
            return True
        if err:
            raise TypeError('{} not allowed in mapping'.format(type(value)))
        return False

    def _check_key_or_value_type(self, obj, iskey):
        """
        Check if the object is of a proper key or value type, depending
        on the iteration count.

        If `iskey` is :py:obj:`True`, the object must be a key. All
        subsequent iterations return :py:obj:`True` if the object is a
        key, :py:obj:`False` if it is a valid value, and raise an error
        if it is neither.
        """
        check = self._check_key_type(obj, err=iskey)
        if check:
            return True
        return not self._check_value_type(obj, err=True)


def option_lookup(name, mapping, option, key_func=None, value_func=None,
                  err_type=ValueError, key_err=KeyError):
    """
    Perform a lookup of an option in a mapping whose keys represent
    the valid options.

    If an invalid option is selected, it an `err_type` error is raised
    (:py:exc:`ValueError` by default).

    Parameters
    ----------
    name : str
        The name of the mapping to display if an error occurs. If the
        option is a function argument, the name of the argument is a
        good name choice.
    mapping : mapping
        The mapping to perform a the lookup in.
    option : object
        The key to look up in mapping.
    key_func : callable or None
        The transformation to apply to `option` to obtain the actual
        key to look up. If :py:obj:`None` (the default), no
        transformation is done. A common choice for this argument is
        :py:meth:`str.casefold` or :py:meth:`str.lower`, for
        case-insensitive string keys.
    value_func : callable or None
        The transformation to apply to the value that is found. If
        :py:obj:`None` (the default), no transformation is done. If
        supplied, must be a callable that accepts three arguments:

        - ``option``
        - ``key``: ``option`` transformed by ``key_func``
        - ``value``: The raw value retreived from the dictionary.

    err_type : type
        The type of the :py:exc:`Exception` to raise. Default is
        :py:exc:`ValueError`.
    key_err : type or tuple[type]
        The type of error expected from a failed lookup in `mapping`.
        If multiple types are to be expected, a :py:class:`tuple` of
        types may be supplied. Defaults to :py:exc:`KeyError`.
    """
    with ErrorTransform(key_err, err_type, 'Invalid value for `{0}`: {1!r}',
                        name, option):
        key = option if key_func is None else key_func(option)
        value = mapping[key]
    # This is not in the exception handler because its your own fault:
    # Option can be anything since its user supplied, but not mapping values
    if value_func is not None:
        value = value_func(option, key, value)
    return value


class mapping_context:
    """
    A context manager for temporarily modifying the keys of a
    mapping.

    The context manager has a :py:meth:`delete` method that allows
    values to be removed as well. The method accepts any number of
    attribute names to delete and returns the context manager, so it can
    be used in a :ref:`with` block directly. Missing key names are
    ignored.

    All mapping values are reset to their original values when the
    manager exits. Nesting multiple instances of this context manager
    has a cumulative effect.

    The context manager is reentrant: the manager can be entered and
    exited and modified before re-entry as many times as necessary.

    Sample usage::

        d = {'a': 1, 'b': 2}
        print(d)
        with mapping_context(d, b=0, c=3):
            print(d)
            with mapping_context(d, b=1).delete('a'):
                print(d)
            print(d)
        print(d)

    Will result in::

        {'a': 1, 'b': 2}
        {'a': 1, 'b': 0, 'c': 3}
        {'b': 1, 'c': 3}
        {'b': 0, 'c': 3, 'a': 1}
        {'b': 2, 'a': 1}

    Instances have three documented attributes:

    .. py:attribute:: mapping

       The :py:class:`dict`\ -like object that this context manager
       applies to. The entire interface to the mapping is through the
       :py:meth:`getfunc` and :py:meth:`setfunc` methods, so that a
       context manager for non-mapping types can be simulated by
       subclassing.

    .. py:attribute:: updates

       A mapping of the added keys to their prior values. This mapping
       is unordered.

    .. py:attribute:: sentinel

       A special marker object guaranteed not to exists in the original
       mapping, used to mark deleted keys.
    """
    __slots__ = ('mapping', 'updates', 'sentinel')

    def __init__(self, mapping, *args, **kwargs):
        """
        Initialize a new context manager to replace the
        specified elements of the given mapping.

        Positional arguments represent mappings that contain keys and
        values to replace or add, each one in a format that would be
        accepted by :py:meth:`dict.update`.

        Keyword arguments are individual keys to update.
        """
        self.sentinel = object()
        self._init(mapping, *args, **kwargs)

    def __enter__(self):
        """
        Enter the context manager by updating the requested
        elements, return the context manager itself.
        """
        for key, value in self.updates.items():
            self.updates[key] = self.getfunc(key)
            self.setfunc(key, value)
        return self

    def __exit__(self, *args, **kwargs):
        """
        Restore the elements of the mapping.
        """
        # Convert to list to avoid modification during iteration
        for item in self.updates.items():
            self.setfunc(*item)

    def delete(self, *keys):
        """
        Remove all the keys named in ``keys`` from the mapping, but keep
        a record of them to be restored on exit.

        Return the context manager itself.
        """
        for key in keys:
            self.updates[key] = self.sentinel
        return self

    def chain(self, *args, **kwargs):
        """
        Create a chained :py:class:`mapping_context` with the same
        mapping class and :py:attr:`sentinel` object as this mapping.

        This method allows the example in the class docs to be rewritten
        as::

            d = {'a': 1, 'b': 2}
            print(d)
            with mapping_context(d, b=0, c=3) as mc:
                print(d)
                with mc.chain(b=1).delete('a'):
                    print(d)
                print(d)
            print(d)

        Returns a new :py:class:`mapping_context`.
        """
        cls = type(self)
        dc = cls.__new__(cls)
        dc.sentinel = self.sentinel
        dc._init(self.mapping, *args, **kwargs)
        return dc

    def _init(self, mapping, *args, **kwargs):
        """
        Sets ``mapping`` and records the modified and added keys
        similarly to :py:meth:`dict.update`, except that it allows
        multiple positional arguments, which may be of mixed types.
        Arguments are added in the following order:

        1. ``args`` is processed in order. Each element is added in the
           order of its iterator.
        2. ``kwargs`` is added in the order of its iterator.

        Later duplicate keys silently override earlier ones.
        """
        self.mapping = mapping
        self.updates = {}
        for arg in args:
            self.updates.update(arg)
        self.updates.update(kwargs)

    def getfunc(self, key):
        """
        A customizable function to get a single element of the mapping.

        If `key` is not present, this function must return
        :py:attr:`sentinel`.

        The default implementation works for most Python builtin mapping
        types that support a :py:meth:`~dict.get` method.
        """
        return self.mapping.get(key, self.sentinel)

    def setfunc(self, key, value):
        """
        A customizable function to set a single element of the mapping.

        If value is :py:attr:`sentinel`, the element should be deleted.

        The default implementation works for most Python builtin mapping
        types that support :py:meth:`~object.__delitem__` and
        :py:meth:`~object.__setitem__` methods.
        """
        if value is self.sentinel:
            del self.mapping[key]
        else:
            self.mapping[key] = value


class object_context(mapping_context):
    """
    An extension of :py:class:`mapping_context` that is tailored for
    mutable objects that support :py:func:`getattr`, :py:func:`setattr`
    and :py:func:`delattr`.
    """
    __slots__ = ()

    def getfunc(self, key):
        """
        Mapping getter customized for :py:class:`object` instead of
        :py:class:`dict`.
        """
        return getattr(self.mapping, key, self.sentinel)

    def setfunc(self, key, value):
        """
        Mapping setter and deleter customized for :py:class:`object`
        instead of :py:class:`dict`.
        """
        if value is self.sentinel:
            delattr(self.mapping, key)
        else:
            setattr(self.mapping, key, value)


class _NamespaceOverrideContext(object_context):
    """
    An extension of :py:class:`object_context` designed specifically for
    :meth:`Namespace.override`.

    The inputs are restricted to keywords only, and the managed object
    is returned instead of the context manager.
    """
    __slots__ = ()

    def __init__(self, namespace, **kwargs):
        """
        Initialize a new context manager to replace the specified
        elements of the given namespace.
        """
        super().__init__(namespace, **kwargs)

    def __enter__(self):
        """
        Enter the context manager and return the mapping rather than
        `self`.
        """
        return super().__enter__().mapping


class Namespace:
    """
    A simple namespace object.

    The class is mutable. It implements containment checks. It can be
    converted to a dictionary using :py:func:`vars`. That being said, it
    supports a dictionary-like interface for elements whose names are not
    valid python identifiers, or are shadowed by descriptors.

    This class originated with :py:class:`argparse.Namespace` and
    :py:class:`types.SimpleNamespace`.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a new namespace with the specified named arguments.

        Key-value pairs in each iterable of `args` are added in order,
        followed by the mapping `kwargs`.
        """
        for arg in args:
            self.__dict__.update(arg)
        self.__dict__.update(kwargs)

    def __contains__(self, name):
        """
        Check if the namespace contains `name`.
        """
        return name in self.__dict__

    def __eq__(self, other):
        """
        Check if this object is equal to another namespace.

        Two namespaces are considered equal if they are both subclasses
        of :py:class:`Namespace` and contain the same mappings.
        """
        if not isinstance(other, __class__):
            return NotImplemented
        return self.__dict__ == other.__dict__

    def __repr__(self):
        """
        Returns a usable string representation of this namespace.
        """
        return '{}({!r})'.format(type(self).__name__, self.__dict__)

    def __getitem__(self, key):
        """
        Retrieve an item directly from the dictionary.

        Useful for items whose names are not valid python identifiers.

        Parameters
        ----------
        key :
            The key of the object to retreive. Does not have to be a
            string.

        Return
        ------
        object :
            The value mapped to the specified key. Raises an error if
            the key is not found.
        """
        return self.__dict__[key]

    def __setitem__(self, key, value):
        """
        Set an item directly into the dictionary.

        Useful for items whose names are not valid python identifiers.

        Parameters
        ----------
        key :
            The key of the object to retreive. Does not have to be a
            string.
        value :
            The value mapped to the specified key.
        """
        self.__dict__[key] = value

    def __delitem__(self, key):
        """
        Delete a mapping directly from the dictionary.

        Useful for items whose names are not valid python identifiers.

        Parameters
        ----------
        key :
            The key of the mapping to delete. Does not have to be a
            string.
        """
        del self.__dict__[key]

    def __len__(self):
        """
        The number of items in this namespace.
        """
        return len(self.__dict__)

    def get(self, key, default=None):
        """
        :py:class:`dict`-like :py:meth:`~dict.get` operation on the
        namespace's mapping.
        """
        return self.__dict__.get(key, default)

    def setdefault(self, key, value):
        """
        :py:class:`dict`-like :py:meth:`~dict.setdefault` operation on
        the namespace's mapping.
        """
        return self.__dict__.setdefault(key, value)

    def items(self):
        """
        An iterator over the items in this namepace's mapping.
        """
        return self.__dict__.items()

    def override(self, **kwargs):
        """
        Returns a context manager that can be used to temporarily set
        attributes in this namespace.

        The context manager has a `delete` method that allows values
        to be removed as well. The method accepts any number of
        attribute names to delete and returns the context manager, so it
        can be used in a :ref:`with` block directly. Missing key names
        are ignored.

        The context manager is a modified version of
        :py:class:`mapping_context`, so it also has a
        :py:meth:`~mapping_context.chain` method.

        All values will be reset to their original values when the
        manager exits. All context managers returned by this method
        operate on the same object, so their effects are cumulative.

        Sample usage::

            n = Namespace(a=1, b=2)
            print(n)
            with n.override(b=0, c=3):
                print(n)
                with n.override(b=1).delete('a'):
                    print(n)
                print(n)
            print(n)

        Will result in::

            Namespace(a=1, b=2)
            Namespace(a=1, b=0, c=3)
            Namespace(b=1, c=3)
            Namespace(b=0, c=3, a=1)
            Namespace(b=2, a=1)
        """
        return _NamespaceOverrideContext(self, **kwargs)
