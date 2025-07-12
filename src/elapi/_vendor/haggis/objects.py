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
Functions for manipulating the structure of objects.

This includes things like spoofing module contents, copying classes and
functions, and automatically creating properties.
"""

__all__ = [
    'HiddenPropMeta', 'copy_func', 'copy_class', 'getsizeof',
    'package_root', 'size_type_mapping', 'update_module',
]


from array import array
from collections.abc import Iterable, Mapping
from copy import copy
from functools import update_wrapper, WRAPPER_ASSIGNMENTS
from itertools import chain
from os.path import basename, dirname
import sys
from types import FunctionType, ModuleType


#: List mapping of types to the special processing routines required to
#: support them with :py:func:`getsizeof`.
#:
#: Types are checked from the end of the list. The first element is
#: :py:class:`~collections.abc.Iterable`, which is the universal
#: catchall. Later elements are more specific types. Custom types
#: should be appended to the end.
#:
#: The following types are supported out of the box:
#:
#: - :py:class:`~collections.abc.Iterable`
#: - :py:class:`~collections.abc.Mapping`
#: - :py:class:`str`, :py:class:`bytes`, :py:class:`bytearray`,
#:   :py:class:`array.array`
#: - :py:class:`numpy.ndarray`
#:
#: The list contains two-element tuples, as would be used to initialize
#: a :py:class:`dict`. The first element can be a scalar type or tuple
#: of types. The second element may be `None`, indicaing a passthrough
#: to :py:func:`sys.getsizeof`, or a callable accepting an object of
#: the correct type, returning an iterable of elements in any order.
#: The callable only needs to iterate the top-level elements.
#:
#: Permanently register handlers by appending the appropriate tuple to
#: this list. Temporarily register them by using the `handlers`
#: argument to :py:func:`getsizeof`.
size_type_mapping = [
    (Iterable, iter),
    (Mapping, lambda m: (e for i in m.items() for e in i)),
    ((str, bytes, bytearray, array), None),
]


try:
    import numpy
except ImportError:
    pass
else:
    def ndarray_handler(x):
        """
        Yield all the elements of the array that are objects.

        Structured dtypes are parsed field-by-fiels, with proper
        handling of nested structures.

        Parameter
        ---------
        x : numpy.ndarray
            The array to parse.

        Return
        ------
        elem :
            A generator of all the elements of `x` that have dtype code
            ``'O'``.
        """
        def dfs(x):
            """
            DFS chosen because nested datatypes are expected to be of
            limited deoth, and because it's most likely to return the
            fields and subarrays in order of increasing offset.

            Parameter
            ---------
            x : numpy.ndarray
                An array potentially containing objects.

            Return
            ------
            elem :
                An generator chaining the elements of the array that
                are objects together.
            """
            dtype = x.dtype
            if not dtype.hasobject:
                return

            # Structure
            if dtype.fields is not None:
                for name in dtype.fields:
                    yield from dfs(x[name])
            # Array
            elif dtype.subdtype is not None:
                for i in numpy.arange(numpy.prod(dtype.shape)):
                    yield from dfs(x[i])
            # Primitive
            else:
                yield from map(numpy.ndarray.item, numpy.nditer(x, flags=['refs_ok']))

        yield from dfs(x)

    size_type_mapping.append((numpy.ndarray, ndarray_handler))


def getsizeof(obj, handlers=None, default=sys.getsizeof(int)):
    """
    Recursive version of :py:func:`sys.getsizeof` for handling
    iterables and mappings.

    Supports automatic circular reference detection, and does not
    double-count repeated references. String and array types get
    special treatement: they are iterable, but not processed
    recursively because their size already includes the buffer. The
    following types are treated as array types:

    - :py:class:`str`
    - :py:class:`bytes`
    - :py:class:`bytearray`
    - :py:class:`array.array`
    - :py:class:`numpy.ndarray`

    Additional array/string-like types may be added by appending them
    to the module-level tuple :py:attr:`size_type_mapping`. Numpy
    arrays require special treatment because they can contain
    references to other objects nested at arbitrarily deep levels of
    the datatype.

    References are not fully supported yet, but a custom handler can
    be added to :py:attr:`size_type_mapping`. Object attributes have
    only rudimentary support via recursion into ``__dict__`` and
    ``__slots__`` (not necessarily mutually exclusive). Additional
    support is available via custom implementations of
    :py:meth:`~object.__sizeof__`, or through custom handlers.

    Parameters
    ----------
    obj :
        The object whose size is to be computed.
    handlers : None, Iterable[tuple[type, callable]], Mapping
        Mapping of types to handler functions, or list of tuples
        containing type-handler pairs. Items are iterated in reverse
        order, so place more specific types last. Callables must
        accept the object whose elements are to be sized, and return
        an iterable of the top-level elements. Any handlers speciied
        through this argument supersede defaults set in
        :py:attr:`size_type_mapping`.
    default : int
        The default size to use for objects that do not support a
        :py:meth:`~object.__sizeof__` operation. Default:
        ``sys.getsizeof(int)``.

    Return
    ------
    size : int
        The size of the object and all the references it contains.
        This is especially useful for container types.

    Notes
    -----
    This recipe is inspired by Raymond Hettinger's "Compute Memory
    footprint of an object and its contents" available at
    https://github.com/ActiveState/recipe-577504-compute-mem-footprint
    and https://code.activestate.com/recipes/577504/. This function was
    originally written at https://stackoverflow.com/a/70793151/2988730.
    Things I took from Raymond's recipe after the fact:

    - Making handlers iterate through the elements instead of applying
      the original recursion function directly.
    - Using a default value.
    - Accepting a mapping of extra handlers.

    Things I added:

    - Proper handling of strings, bytes and bytearrays
    - Numpy array handler
    - Global type registry
    - Support for `__dict__` and `__slots__`
    """
    if handlers is None:
        handlers = ()
    elif isinstance(handlers, Mapping):
        handlers = handlers.items()

    seen = set()
    def recurse(obj):
        x = id(obj)
        if x in seen:
            return 0
        seen.add(x)
        size = sys.getsizeof(obj, default)

        for type, method in chain(reversed(handlers),
                                  reversed(size_type_mapping)):
            if isinstance(obj, type):
                if method is not None:
                    for elem in method(obj):
                        size += recurse(elem)
                break

        if hasattr(obj, '__dict__'):
            size += recurse(vars(obj))
        for slot in getattr(obj, '__slots__', ()):
            if hasattr(obj, slot):
                size += recurse(getattr(obj, slot))
        return size

    return recurse(obj)


def package_root(module):
    """
    Find the directory containing the root package in which a module is
    defined.

    Only works for modules with a valid ``__file__`` attribute.

    Parameters
    ----------
    module : str or ~types.ModuleType
        The module to investigate. If a name is passed in, the module
        must exist in :py:obj:`sys.modules`.

    Return
    ------
    path : str
        The root path of the package containing the module.
    """
    if isinstance(module, str):
        module = sys.modules[module]
    name = module.__name__
    path = module.__file__
    if basename(path) == '__init__.py':
        path = dirname(path)
    for _ in range(name.count('.') + 1):
        path = dirname(path)
    return path


def update_module(current, other, recurse=False):
    """
    Updates the dict of the module `current` with the dict of
    `other`.

    Either input may be a string (full name as given by ``__name__``),
    or a module reference.

    All functions and classes in `other` whose module is `other`
    will by default be copied and reassigned to `current`. All other
    non-dunder attributes will be copied exactly. Dunder attributes will
    be skipped, except ``__all__``, which will be shallow-copied as a
    list.

    Any attributes already defined in `current` will be skipped. This
    ensures that the globals defined in new methods will be updated
    correctly for the new module.

    If `recurse` is set to :py:obj:`True`, any sub-modules of `other`
    will be copied using this method instead of referenced directly.
    """
    def getmod(mod):
        if isinstance(mod, str):
            return sys.modules[mod]
        # Ducktype non-string objects. This allows things like
        # classes spoofing a module to pass through just fine.
        return mod
    current = getmod(current)
    other = getmod(other)
    cn, on = current.__name__, other.__name__
    cd = current.__dict__
    for name, item in other.__dict__.items():
        if name in cd:
            continue
        if name.startswith('__') and name.endswith('__'):
            if name == '__all__':
                try:
                    item = item[:]
                except Exception:
                    pass
            else:
                continue
        elif isinstance(item, FunctionType):
            if item.__module__ == on:
                item = copy_func(item, cd, cn)
        elif isinstance(item, type):
            if item.__module__ == on:
                item = copy_class(item, cd, cn)
        elif isinstance(item, ModuleType) and recurse:
            if item.__name__.startswith(on + '.'):
                mod = ModuleType(item.__name__.replace(on, cn), item.__doc__)
                update_module(mod, item, recurse)
                sys.modules[mod.__name__] = mod
                item = mod
        cd[name] = item


def copy_class(c, globals=None, module=None):            
    """
    Creates a shallow copy of a class object, optionally replacing
    its module and the object its methods reference for globals.

    This function is useful when importing a class into another
    module, and having it behave as a class of the importing module::

        from mod import cls
        cls = copy_class(cls, globals(), __name__)

    Parameters
    ----------
    c : type
        The class to copy
    globals : dict or None
        If :py:obj:`None`, copy the global dictionaries referenced by
        the methods unchanged. A popular alternative is ``globals()``.
    module : str or None
        The name of the module that this class belongs to. If
        :py:obj:`None`, keep ``c.__module__`` and the modules of all
        methods directly. A popular alternative is ``__name__``.

    Notes
    -----
    This function may not work properly for classes whose metaclass does
    not invoke :py:meth:`type.new <object.__new__>` at some point in the
    construction process.

    Based on https://stackoverflow.com/a/49157516/2988730.
    """
    if module is None:
        module = c.__module__
    attrs = dict(c.__dict__)
    for name, item in c.__dict__.items():
        if isinstance(item, type):
            attrs[name] = copy_class(item, globals, module)
        elif isinstance(item, FunctionType):
            attrs[name] = copy_func(
                item, item.__globals__ if globals is None else globals, module
            )
    d = type.__new__(type(c), c.__name__, c.__bases__, attrs)
    d.__module__ = module
    return d


def copy_func(f, globals=None, name=None, module=None):
    """
    Creates a shallow copy of a function object, optionally replacing
    the object it references for its globals.

    This function is useful when importing a function into another
    module, and having it behave as a function of the importing module::

        from mod import func
        func = copy_func(func, globals(), module=__name__)

    Parameters
    ----------
    f : function
        The object to copy
    globals : dict or None
        If :py:obj:`None`, copy the global dictionary referenced by
        `f`. A popular alternative is ``globals()``.
    name : str or None
        The name to assign to the new function. If None, copy
        ``f.__name__`` directly.
    module : str or None
        The name of the module that this function belongs to. If
        :py:obj:`None`, copy ``f.__module__`` directly. A popular
        alternative is ``__name__``.

    Notes
    -----
    Based originally on https://stackoverflow.com/a/13503277/2988730,
    and updated in https://stackoverflow.com/a/49077211/2988730.
    """
    g = FunctionType(f.__code__,
                     f.__globals__ if globals is None else globals,
                     name=f.__name__ if name is None else name,
                     argdefs=f.__defaults__, closure=f.__closure__)
    g = update_wrapper(g, f)
    if module is not None:
        g.__module__ = module
    g.__kwdefaults__ = copy(f.__kwdefaults__)
    return g


class HiddenPropMeta(type):
    """
    Creates a class with "hidden" read-only properties named in the
    :py:attr:`__hidden_properties__` attribute.

    A hidden property is one that stores its value under a 
    :py:attr:`~object.__dict__` key with the same name. This meta-class
    is therefore incompatible with anything that uses
    :py:obj:`~object.__slots__`.

    .. py:attribute:: __hidden_properties__

       This can be a single string, an iterable of strings, or an
       iterable of two-element tuples containing a string name and an
       initial value. Strings and tuples may be mixed together in an
       iterable. The attribute will be removed from the class body by
       this metaclass after it is processed.

    If the class has an explicit ``__init__`` method defined, it will be
    properly decorated to set the default values of the hidden
    properties. If an explicit ``__init__`` is not found, the implicit
    ``super.__init__`` constructor will be decorated in the same way and
    set as the initializer.
    """
    def __new__(meta, name, bases, body, **kwargs):
        if '__hidden_properties__' in body:
            props = body['__hidden_properties__']
            del body['__hidden_properties__']
            if isinstance(props, str):
                props = [props]

            def check_prop(prop):
                """
                Check if `prop` is a string or a 2-element tuple and
                returns a 2-element tuple. The first element must be a
                string, the second defaults to :py:obj:`None`.
                """
                if isinstance(prop, str):
                    return (prop, None)
                if not isinstance(prop, tuple) or len(prop) != 2 or \
                   not isinstance(prop[0], str):
                    raise ValueError(
                        'property description must be name or name-value tuple'
                    )
                return prop

            props = dict(check_prop(prop) for prop in props)

            def fget(name):
                """
                Create the getter for a given property name.
                """
                def getter(self):
                    return self.__dict__[name]
                getter.__name__  = name
                getter.__doc__ = f'Retrieves {name} as a read-only property.'
                return getter

            for prop in props:
                if prop not in body:
                    body[prop] = property(fget(prop))
                elif not isinstance(body[prop], property):
                    raise ValueError(
                        'property {!r} shadows non-property '
                        'attribute'.format(prop)
                    )
        else:
            props = None

        cls = super().__new__(meta, name, bases, body)
        if props:
            def wrapper(parent, initializer):
                def  __init__(self, *args, **kwargs):
                    self.__dict__.update(initializer)
                    return parent(self, *args, **kwargs)

                update_wrapper(
                    __init__, parent, tuple(
                        x for x in WRAPPER_ASSIGNMENTS if x != '__qualname__'
                    )
                )
                __init__.__qualname__ = '.'.join(
                    (cls.__qualname__, '__init__')
                )
                return __init__
            setattr(cls, '__init__', wrapper(getattr(cls, '__init__'), props))
        return cls
