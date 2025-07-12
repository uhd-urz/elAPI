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
Recipes for handling different types of configuration files.
"""


__all__ = [
    'JSONConfiguration', 'JSONObject', 'NumpyObject', 'json_registry'
]


from collections.abc import Mapping
from io import StringIO
from json import load
from numbers import Number
from os import replace, sep
from os.path import isfile
from sys import maxsize, stdout

import numpy as np

from .files import open_file
from .mapping import Namespace
from .recipes import islast
from .structures import Trie


class JSONObject:
    """
    Base class of additional output formatting types.

    To register a new formatter use the module-level
    :py:meth:`json_registry.register` function.

    .. py:attribute:: type

       The type or types supported by this formatter. Any object that is
       a valid second argument to :py:func:`isinstance` is accepted.
    """
    __slots__ = ('type')

    def __init__(self, type):
        """
        Create a formatting object for the specified type.

        Parameters
        ----------
        type : type or tuple
            The permitted type or types. Any object that is a valid
            second argument to :py:func:`isinstance` is accepted.
        """
        self.type = type

    def format(self, file, obj, prefix, indent, linewidth):
        """
        Format an object for output to a file.

        The base class method is a no-op and should be overriden by
        subclasses.

        Parameters
        ----------
        file : file-like
            An open file-like object to write to.
        obj :
            An instance of :py:attr:`type` to format.
        prefix : str
            The line prefix (current indentation) to start with.
        indent : int
            The number of spaces to use for any additional indents.
        linewidth : int
            Number of characters to attempt to wrap lines at.
        """
        pass


class NumpyObject(JSONObject):
    """
    Type of :py:class:`JSONObject` speficic to numpy arrays.

    An instance of this class is registered automatically.
    """

    #: Format spec to use for numpy arrays.
    #:
    #: Must not contain a ``'prefix'`` key, which will be silently
    #: purged if present.
    _PRINTOPTS = {
        'separator': ', ',
        'floatmode': 'fixed',
        'precision': 18,
        'suppress_small': False,
        'threshold': maxsize,
        'sign': ' ',
        'max_line_width': 120,
        'formatter': {
            'bool': lambda x: str(x).lower()
        }
    }

    def __init__(self, printopts=None, type=np.ndarray):
        """
        Create an instance with the specified print options.

        Parameters
        ----------
        printopts : dict, optional
            A formatting spec that contains the keyword arguments to
            :py:func:`numpy.array2string`. All keys listed are
            allowed, except ``'prefix'``. The default is to use the
            builtin formatting spec.
        """
        super().__init__(type=type)
        if printopts:
            self.printopts = self._PRINTOPTS.copy()
            self.printopts.update(printopts)
        else:
            self.printopts = self._PRINTOPTS
        self.printopts.pop('prefix', None)

    def format(self, file, obj, prefix, indent, linewidth):
        """
        Pretty-print a numpy array with the specifed indentation.
        """
        prefix += ' ' * indent
        printopts = self.printopts.copy()
        printopts['max_line_width'] = linewidth
        array_string = np.array2string(obj, prefix=prefix, **printopts).replace('\n\n', '\n').replace(' \n', '\n')
        if array_string[0] == '[' \
          and array_string[-1] == ']' \
          and (
            len(s := array_string.splitlines()) > 1 \
            or max(map(len, s)) > linewidth - (len(prefix) + indent)
          ):
            file.write('[\n ')
            file.write(prefix)
            file.write(array_string[1:-1])
            file.write('\n')
            file.write(prefix[:-indent])
            file.write(']')
        else:
            file.write('\n')
            file.write(prefix)
            file.write(array_string)


class _JSONRegistry(list):
    def register(self, obj):
        self.append(obj)


#: A list-like object with an additional
#: :py:meth:`~json_registry.register` method.
#:
#: .. py:method:: json_registry.register(formatter: JSONObject)
#:
#:    Call this function to add output types to be used with
#:    :py:meth:`JSONConfiguration._pprint`.
#:
#: .. py:method:: json_registry.clear()
#:
#:    Call this function to clear the registry.
#:
#: An instance of :py:class:`NumpyObject` with default parameters is
#: registered automatically.
json_registry = _JSONRegistry()

del _JSONRegistry


json_registry.register(NumpyObject())


def _make_trie(iterable):
    """
    Add all the items in `iterable` into a
    :py:class:`~haggis.structures.Trie`. Hashable elements are treated
    as single top-level leaves. Lists are treated as nested items.
    """
    t = Trie()
    for item in iterable:
        if not isinstance(item, list):
            item = [item]
        t.add(item)
    return t


class JSONConfiguration(Namespace):
    """
    Class for managing loading and updating JSON configurations.

    The file into its just loaded into the namespace `__dict__`. The
    metadata attributes are stored in `__slots__`, so do not interfere
    with the configuration keys. In particular, the following metadata
    key is supported:

    .. py:attribute:: _source

       The source file or mapping for the configuration.

    Child classes should extend :py:meth:`_reload` to parse the necessary
    keys directly in their own namespace, and to do any error checking
    on the loaded data. Conversely, children should extend
    :py:meth:`_update` to perform any additional steps necessary to
    serialize back into a file.

    Methods and attibutes are not private: the single underscores are
    intended to reduce the probablility of shadowing a configuration
    key.
    """
    __slots__ = ('_source',)

    def __init__(self, source):
        """
        Initialize a new instance with the specified source.

        Parameters
        ----------
        source : str or Path or Mapping
            If a mapping type, use to update the instance
            dictionary directly. Otherwise assume filename or path.
        """
        self._reload(source)

    def __repr__(self):
        """
        Return a programmatic representation of this configuration.

        Returns
        -------
        str
            A string representation of the object.
        """
        if isinstance(self._source, str) and sep in self._source:
            f = "r'{}'".format(self._source)
        else:
            f = repr(self._source)
        return '{}({})'.format(type(self).__name__, f)

    def __str__(self):
        """
        A detailed, expanded, representation of this configuration.

        Returns
        -------
        str :
            A string containing the contents of this mapping.
        """
        s = StringIO()
        self._pprint(s)
        return s.getvalue()

    def _reload(self, source=None):
        """
        Load the specified file (or the default :py:attr:`_filename`).

        Any nested mapping objects are replaced with
        :py:class:`~haggis.mapping.Namespace`.

        Override this method to implement additional conversion or
        error checking functionality.

        Parameters
        ----------
        source : str or Path or Mapping, optional
            If supplied, replace the default source for this
            configuration.
        """
        def emplace(mapping):
            """ Convert all nested dicts to Namespaces """
            for k, v in mapping.items():
                if isinstance(v, Mapping):
                    v = Namespace(emplace(v))
                yield k, v

        if source:
            self._source = source
        self.__dict__.clear()
        if isinstance(self._source, Mapping):
            data = self._source
        else:
            with open(self._source, 'r') as f:
                data = load(f)

        self.__dict__.update(emplace(data))

    def _update(self, source=None, *exclude):
        """
        Write the dictionary back to the file or original mapping.

        If writing to a mapping, convert nested
        :py:class:`~haggis.mapping.Namespace`\\ s to :py:class:`dict`.

        Override this method to implement additional conversion or
        error checking functionality.

        Parameters
        ----------
        source : str or Path or Mapping, optional
            If provided, supplies a non-default destination for the
            namespace, but does not permanently replace
            :py:attr:`_source`. The default is `None`.
        *exclude :
            sequence of keys to exclude. Hashable types are keys in the
            current dictionary. Lists indicate multi-level keys. For
            example, to avoid printing ``self.a.b``, add an exclude
            ``['a', 'b']``.
        """
        if not source:
            source = self._source

        if isinstance(source, Mapping):
            exclude = _make_trie(exclude)
            def unplace(prefix, d):
                for k, v in d.items():
                    item = prefix + [k]
                    if item in exclude:
                        continue
                    if isinstance(v, Namespace):
                        v = dict(unplace(item, v.__dict__))
                    yield k, v
            source.clear()
            source.update(unplace([], self.__dict__))
        else:
            if isfile(source):
                end = b'.bak' if isinstance(source, (bytes, bytearray)) else '.bak'
                replace(source, source + end)
            self._pprint(source, exclude=exclude)

    def _check_path(self, *keys):
        """
        Ensure that a given sequence of nested namespaces exists in
        this namespace.

        All keys in the sequence besides the last one must contain a
        mutable :py:attr:`~object.__dict__`. If the last item in the
        sequence does not exist, it will be created as a
        :py:class:`~haggis.mapping.Namespace`.

        Parameters
        ----------
        *keys :
            Sequence of keys to verify. Any missing keys will be
            created as empty namespaces. An error will be raised if
            an intermediate object exists without a mutable `__dict__`.

        Return
        ------
        The object at the end of the chain. If `keys` is empty, returns
        the current object.
        """
        obj = self
        for key in keys:
            if key not in obj.__dict__:
                obj.__dict__[key] = Namespace()
            obj = obj.__dict__[key]
        return obj

    def _pprint(self, filename=None, *, indent=4, root_indent=False, linewidth=120,
                float_format='', int_format='', bool_format=True,
                bytes_format='utf-8', exclude=()):
        """
        Pretty print the configuration into a file.

        All arguments besides the file name are keyword-only. Output
        formats for additional datatypes besides the normal JSON types
        are supported by registering :py:class:`JSONObject` descriptors
        using :py:meth:`json_registry.register`.

        Parameters
        ----------
        filename : str or Path or file-like
            The file to write to. If an open file, must have write
            permissions. If a string or path, will be truncated or
            created (using ``'w'`` mode).
        indent : int
            The number of spaces to indent nested objects by. Default 4.
        root_indent : bool
            Whether or not to indent the root namespace. Default is not
            to.
        linewidth : int
            The number of characters to attempt to wrap arrays at.
            Default is 120.
        bytes_format : str
            Name of the encoding to use to convert byte arrays to
            string. If `None`, record byte arrays as arrays of
            hexadecimal integers.
        exclude : iterable
            An iterable of items to exclude from the printout. Hashable
            elements are interpreted as top-level keys. Nested elements
            must be specified as a list of keys.
        """
        def iscontainer(e):
            return isinstance(e, (dict, list, tuple, np.ndarray))

        def strlen(e):
            if isinstance(e, str):
                return len(e)
            if isinstance(e, (bytes, bytearray)):
                if bytes_format is None:
                    return 4 + 6 * len(e)
                return len(e.decode(bytes_format))
            return 0

        def pprint_object(obj, key, spaces):
            """
            Spaces is the indented number of spaces!

            Why: this allows the root element to have zero indentation while
            all the other elements have correct indentation.
            """
            f.write('{\n')
            if key is None:
                iterator = obj.items()
            else:
                iterator = ((k, v) for k, v in obj.items() \
                                            if key + [k] not in exclude)
            for last, (k, v) in islast(iterator):
                f.write(spaces)
                f.write('"' + str(k) + '":')
                f.write(' ')

                pprint_element(v, None if key is None else key + [k], spaces)
                if not last:
                    f.write(',\n')

            spaces = '' if len(spaces) <= indent else spaces[:-indent]
            f.write('\n' + spaces + '}')

        def pprint_array(arr, spaces):
            more_spaces = spaces + ' ' * indent
            f.write('[')

            multiline = (
                any(map(iscontainer, arr)) or
                sum(map(strlen, arr)) + 2 * len(arr) +
                                        len(more_spaces) > linewidth
            )

            if multiline:
                prefix = more_spaces
                suffix = '\n'
            else:
                prefix = ''
                suffix = ' '
                spaces = ''
            comma = ',' + suffix

            f.write(suffix)
            for last, e in islast(arr):
                f.write(prefix)
                pprint_element(e, None, more_spaces)
                if not last:
                    f.write(comma)
            f.write(suffix + spaces + ']')

        def pprint_bytes(arr, spaces):
            more_spaces = spaces + ' ' * indent
            f.write('[')

            if 4 + 6 * len(arr) + len(more_spaces) > linewidth:
                prefix = more_spaces
                suffix = '\n'
            else:
                prefix = ''
                suffix = ' '
                spaces = ''
            comma = ',' + suffix

            f.write(suffix)
            for last, b in arr:
                f.write(prefix + '{:%0.2X}'.format(b))
                if not last:
                    f.write(comma)
            f.write(suffix + spaces + ']')

        def pprint_element(e, key, spaces):
            if e is None:
                f.write('null')
            elif isinstance(e, bool):
                if bool_format:
                    f.write(str(e).lower())
                else:
                    f.write(str(int(e)))
            elif isinstance(e, (bytes, bytearray)):
                if bytes_format is None:
                    pprint_bytes(e, spaces)
                else:
                    f.write('"' + esc(e.decode(bytes_format)) + '"')
            elif isinstance(e, str):
                f.write('"' + esc(e) + '"')
            elif isinstance(e, (int, np.integer)):
                f.write('{:{}}'.format(e, int_format))
            elif isinstance(e, Number):
                f.write('{:{}}'.format(e, float_format))
            elif isinstance(e, (list, tuple)):
                pprint_array(e, spaces)
            elif isinstance(e, (dict, Namespace)):
                pprint_object(e, key, spaces + ' ' * indent)
            else:
                for reg in json_registry:
                    if isinstance(e, reg.type):
                        reg.format(f, e, spaces, indent, linewidth)
                        break
                else:
                    raise TypeError(
                        "Don't know how to encode {}".format(type(e).__name__)
                    )

        def esc(s):
            return s.replace('\\', '\\\\')

        exclude = _make_trie(exclude)
        with open_file(filename or stdout, 'w') as f:
            pprint_object(self, [], ' ' * indent * root_indent)
            f.write('\n')
