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
Utilities for implementing, raising and handling exceptions.
"""

__all__ = ['ErrorTransform']


class ErrorTransform:
    """
    A context manager that translates any exceptions into a different
    type with a predefined message. The constructor arguments are
    assigned to class attributes directly.

    .. py:attribute:: in_type

       The exceptions to look for, in any format accepted by an
       ``except`` clause: a single type or a tuple of types.

    .. py:attribute:: out_type

       The type to reraise as.

    .. py:attribute:: message

       A format string containing the message of the rethrown error. The
       string is expected to conform to the :ref:`formatspec`.

    .. py:attribute:: args

       Additional positional arguments to pass to
       :py:meth:`message.format <str.format>`.

    .. py:attribute:: kwargs

       Additional keyword arguments to pass to `message.format`. There
       three dynamic keywords are always passed in:

         - ``type``: The class of the trapped error.
         - ``str``: The result of ``str(exc)`` on the trapped error.
         - ``repr``: The result of ``repr(exc)`` on the trapped error.

       These three names must not appear as keys in `kwargs`.
    """
    def __init__(self, in_type, out_type, message, *args, **kwargs):
        """
        Construct a context manager that will transform `in_type`
        exceptions to `out_type` with the specified formatted message.
        """
        self.in_type = in_type
        self.out_type = out_type
        self.message = message
        self.args = args
        self.kwargs = kwargs

    @classmethod
    def KeyError(cls, out_type, name='dictionary'):
        """
        Create an instance of this class suitable for handling
        occurrences of :py:exc:`KeyError` caused by, e.g. dictionary
        access via :py:meth:`~object.__getitem__`.

        :py:attr:`in_type` is implicitly :py:exc:`KeyError` and `name`
        is the name of the dictionary where the error occurred.
        """
        return cls(KeyError, out_type, "Missing '{str}' from {name}",
                   name=name)

    def __enter__(self):
        """
        Enter the context manager (no-op).
        """
        pass

    def __exit__(self, type, value, traceback):
        """
        Exit the context manager.

        If an exception of type :py:attr:`in_type` occurred, it is
        transformed to an exception of type :py:attr:`out_type` with the
        configured message and raised. All other exception types are
        passed through (this method returns :py:obj:`None`).
        """
        if type is not None and issubclass(type, self.in_type):
            raise self.out_type(
                self.message.format(*self.args, **self.kwargs, type=type,
                                    str=str(value), repr=repr(value))
            ) from value
