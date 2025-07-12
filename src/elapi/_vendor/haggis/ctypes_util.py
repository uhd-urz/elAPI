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
Utilities and recipes for extending ctypes functionality.
"""


__all__ = [
    'c_bool_p', 'c_byte_p', 'c_double_p', 'c_float_p', 'c_int_p',
    'c_int8_p', 'c_int16_p', 'c_int32_p', 'c_int64_p', 'c_long_p',
    'c_longdouble_p', 'c_longlong_p', 'c_short_p', 'c_size_t_p',
    'c_ssize_t_p', 'c_ubyte_p', 'c_uint_p', 'c_uint8_p', 'c_uint16_p',
    'c_uint32_p', 'c_uint64_p', 'c_ulong_p', 'c_ulonglong_p',
    'c_ushort_p',
    'check_zero', 'check_nonzero', 'decode_c_char_p', 'make_enum',
    'to_c_char_p', 'CDLLWrapper',
]


from contextlib import ExitStack
from ctypes import (
    CDLL, POINTER,
    c_int8, c_int16, c_int32, c_int64,
    c_byte, c_short, c_int, c_long, c_longlong,
    c_uint8, c_uint16, c_uint32, c_uint64,
    c_ubyte, c_ushort, c_uint, c_ulong, c_ulonglong,
    c_bool, c_size_t, c_ssize_t,
    c_float, c_double, c_longdouble,
    c_void_p,
)
from os.path import join
from os import name as os_name

from .recipes import CloseableMixin


c_byte_p = POINTER(c_byte)
c_short_p = POINTER(c_short)
c_int_p = POINTER(c_int)
c_long_p = POINTER(c_long)
c_longlong_p = POINTER(c_longlong)

c_int8_p = POINTER(c_int8)
c_int16_p = POINTER(c_int16)
c_int32_p = POINTER(c_int32)
c_int64_p = POINTER(c_int64)

c_ubyte_p = POINTER(c_ubyte)
c_ushort_p = POINTER(c_ushort)
c_uint_p = POINTER(c_uint)
c_ulong_p = POINTER(c_ulong)
c_ulonglong_p = POINTER(c_ulonglong)

c_uint8_p = POINTER(c_uint8)
c_uint16_p = POINTER(c_uint16)
c_uint32_p = POINTER(c_uint32)
c_uint64_p = POINTER(c_uint64)

c_bool_p = POINTER(c_bool)
c_size_t_p = POINTER(c_size_t)
c_ssize_t_p = POINTER(c_ssize_t)
c_float_p = POINTER(c_float)
c_double_p = POINTER(c_double)
c_longdouble_p = POINTER(c_longdouble)


def check_zero(fail_msg, error=ValueError, name_prefix=True):
    """
    Generate an error checker for the specified message and error type.

    The resulting function can be set as the
    :py:attr:`~ctypes._FuncPtr.errcheck` of a :py:mod:`ctypes` function.
    It will raise an error on truthy return values and pass through
    zeros.

    Parameters
    ----------
    fail_msg : str
        Messages may be new-style interpolation strings that index the
        function arguments and include the names ``__func__`` and
        ``__value__`` as a keywords.
    error : type
        The type of error to raise if the result is truthy.
    name_prefix : str or bool
        If `name_prefix` is a string, it gets prepended to the message
        directly. If any other truthy value, ``'{__func__}: '`` gets
        prefixed instead. Falsy values don't modify the message at all.
        String prefixes can contain interpolations themselves.

    Return
    ------
    callable :
        A function named `check_zero` that accepts arguments named
        ``value``, ``func``, and ``arguments`` and raises an error if
        ``value`` is truthy.
    """
    if isinstance(name_prefix, str):
        fail_msg = name_prefix + fail_msg
    elif name_prefix:
        fail_msg = '{__func__}: ' + fail_msg

    def check(value, func, arguments):
        if value:
            raise error(fail_msg.format(
                    *arguments, __func__=func.__name__, __value__=value
                ))
        return value

    check.__name__ = check.__qualname__ = 'check_zero'
    return check


def check_nonzero(fail_msg, error=ValueError, name_prefix=True):
    """
    Generate an error checker for the specified message and error type.

    The resulting function can be set as the
    :py:attr:`~ctypes._FuncPtr.errcheck` of a :py:mod:`ctypes` function.
    It will raise an error on falsy return values and pass through
    the return value otherwise.

    Parameters
    ----------
    fail_msg : str
        Messages may be new-style interpolation strings that index the
        function arguments and include the name `__func__` as a keyword.
    error : type
        The type of error to raise if the result is falsy.
    name_prefix : str or bool
        If `name_prefix` is a string, it gets prepended to the message
        directly. If any other truthy value, ``'{__func__}: '`` gets
        prefixed instead. Falsy values don't modify the message at all.
        String prefixes can contain interpolations themselves.

    Return
    ------
    callable :
        A function named `check_nonzero` that accepts arguments named
        ``value``, ``func``, and ``arguments`` and raises an error if
        ``value`` is falsy.
    """
    if isinstance(name_prefix, str):
        fail_msg = name_prefix + fail_msg
    elif name_prefix:
        fail_msg = '{__func__}: ' + fail_msg

    def check(value, func, arguments):
        if not value:
            raise error(fail_msg.format(*arguments, __func__=func.__name__))
        return value

    check.__name__ = check.__qualname__ = 'check_nonzero'
    return check


def make_enum(enum_type):
    """
    Generate an error checker that converts to the specified enum.

    The resulting function can be set as the
    :py:attr:`~ctypes._FuncPtr.errcheck` of a :py:mod:`ctypes` function.
    It converts the return value into a Python enum.

    Checkers returned by this function are cached, for efficiency when
    using multiple times on the same `enum_type`.

    Parameters
    ----------
    enum_type : callable
        Normally, this is a subclass of :py:class:`IntEnum`, which
        converts a C return value into the appropriate type. However,
        this may be any arbirary callable, as long as it has a
        ``__name__`` attribute.

    Return
    ------
    callable :
        A function named `make_` followed by the ``__name__`` of
        `enum_type` that accepts arguments named ``value``, ``func``,
        and ``arguments`` and converts ``value`` to the target type.
    """
    check = make_enum.registry.get(enum_type)
    if check is None:
        def check(value, func, arguments):
            return enum_type(value)
        make_enum.registry[enum_type] = check
        check.__name__ = check.__qualname__ = 'make_' + enum_type.__name__
    return check

make_enum.registry = {}


def decode_c_char_p(encoding='utf-8', null_error=False):
    """
    Generate an error checker that decodes strings with a custom
    encoding.

    The resulting function can be set as the
    :py:attr:`~ctypes._FuncPtr.errcheck` of a :py:mod:`ctypes` function.
    It decodes the bytes of a `char *` to a python string.

    Checkers returned by this function are cached, for efficiency when
    using multiple times on the same encoding.

    Parameters
    ----------
    encoding : str
        The name of the target encoding.
    null_error : bool
        Whether or not to raise an error on NULL strings. Defaults is
        `False`.

    Return
    ------
    callable :
        A function named `decode_as_` followed by the target encoding
        that accepts arguments named ``value``, ``func``, and
        ``arguments`` and decodes ``value`` using the specified
        encoding.
    """
    key = encoding.casefold().replace('-', '_')
    if null_error:
        key += '_err'
    decoder = decode_c_char_p.registry.get(key)
    if decoder is None:
        if null_error:
            def decode(value, func, arguments):
                if value is None:
                    raise TypeError(f'{func.__name__}: expected string result, but got None')
                return value.decode(encoding)
        else:
            decode = lambda value, func, arguments: value.decode(encoding)
        decode.__name__ = decode.__qualname__ = f'decode_as_{key}'
        decoder = decode_c_char_p.registry[key] = decode
    return decoder

decode_c_char_p.registry = {}


def to_c_char_p(s, encoding='utf-8'):
    """
    Convert a string into a NUL-terminated :py:class:`bytes`.

    Parameters
    ----------
    s : str
        The string to convert.
    encoding : str
        The encoding to use. Default is ``utf-8``.

    Returns
    -------
    bytes
        The encoded string, terminated by ``b'\x00'``.
    """
    if s is None:
        return None
    return s.encode(encoding) + b'\x00'


if os_name == 'nt':
    from ctypes import windll, wintypes
    from os import add_dll_directory as _add_dll_directory
    _close_dll_handle = windll.kernel32.FreeLibrary
    _close_dll_handle.argtypes = [wintypes.HMODULE]
    _close_dll_handle.restype = wintypes.BOOL
    _close_dll_handle.errcheck = check_nonzero('Unable to release module',
                                               WindowsError)
else:
    def add_dll_directory(*args, **kwargs):
        return CloseableMixin()
    _close_dll_handle = CDLL('').dlclose
    _close_dll_handle.argtypes = [c_void_p]
    _close_dll_handle.restype = c_int
    _close_dll_handle.errcheck = check_zero(
        'Unable to release module: error {__value__}', OSError
    )


class CDLLWrapper(CDLL, CloseableMixin):
    """
    Wrapper for full-path DLLs to make them closeable and manage
    dependencies.

    This class is mostly useful for Windows, since it manages
    dependency folders. The only purpose it serves on UNIX-like
    systems is to close the library handle.
    """

    def __init__(self, name, *folders, prefix='', index=None):
        """
        Create a wrapper for the specified library.

        Parameters
        ----------
        name : str
            The basename of the library. Extension is optional.
        folders : str
            Directories containing the dependencies of the main library.
            Ignored on non-Windows systems.
        prefix : str
            The folder relative to which all `folders` should be
            resolved. Default is empty.
        index : int
            The element of `folders` containing the library. If `None`,
            the library name does not require or already has a folder
            prefixed to it.
        """
        if prefix:
            self._folders = tuple(join(prefix, folder) for folder in folders)
        else:
            self._folders = tuple(folders)
        self._basename = name
        self._index = index

        self.open()

    def open(self):
        """
        (Re)open this library, if it is closed.

        If already open, this is a no-op.

        On Windows, the dependency folders are added prior to opening
        the DLL itself.
        """
        if not self._handle:
            lib = self._basename if self._index is None \
                        else join(self._folders[self._index], self._basename)
            with ExitStack() as dependencies:
                for folder in self._folders:
                    dependencies.enter_context(_add_dll_directory(folder))
                CDLL.__init__(self, lib)  # Always open full name
                self._dependencies = dependencies.pop_all()

    def close(self):
        """
        Close this library, if it is open.

        If not open, this is a no-op.

        Any cached function objects are deleted, and the underlying
        binary is closed.

        On Windows, the dependency folders are unloaded after closing
        the DLL itself.
        """
        if self._handle:
            _close_dll_handle(self._handle)
            self._handle = 0
            self._dependencies.close()
    
            # Clear cached objects
            for name, value in list(self.__dict__.items()):
                if isinstance(value, self._FuncPtr):
                    delattr(self, name)
