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
Recipes for common tasks that build on the type of thing normally found
in the builtin :py:mod:`os` module.
"""

__all__ = [
    'Tee', 'StderrTee', 'StdoutTee',
    'add_system_path', 'chdir_context', 'command_line', 'filter_copy',
    'root_path', 'redirect_stderr', 'redirect_stdout',
    'redirect_stream', 'suppress_stderr', 'suppress_stdout',
]


from contextlib import contextmanager
from functools import partial
from os import (
    chdir, close, devnull, dup, dup2, environ, getcwd, pathsep, sep
)
from os.path import abspath, splitdrive
import sys

from .files import open_file
from .string_util import hasspace


def command_line(exec=None, args=None, quote='"'):
    """
    Reconstruct a command line based on the specified executable
    `exec` and iterable of arguments `args`.

    `exec` defaults to :py:obj:`sys.executable` and `args` defaults
    to :py:obj:`sys.argv`.
    """
    def argue(arg):
        """
        Coerce the input to a string and puts quotes around it if it
        contains whitespace.
        """
        arg = str(arg)
        if hasspace(arg):
            return '{}{}{}'.format(quote, arg, quote)
        return arg

    if exec is None:
        exec = sys.executable
    if args is None:
        args = sys.argv

    return '{} {}'.format(argue(exec), ' '.join(map(argue, args)))


def root_path(file=None):
    """
    Retrieve the root file system for the given file, or for the whole
    OS.

    On Windows this will be a drive letter followed by a backslash. On
    most Unix variants, this will just be a slash.
    """
    if file:
        # Modified from http://stackoverflow.com/a/12041606/2988730
        drive, _ = splitdrive(file)
        return drive + sep
    # Courtesy of http://stackoverflow.com/a/22255432/2988730
    return abspath(sep)


def filter_copy(src, dest, hook=None, *, encoding=None, strip_newlines=False):
    """
    Copy a file line by line with optional processing of the lines.

    `src` and `dest` can be either file-like objects or strings or file
    descriptors. If `src` is file-like, it will only be copied from the
    current position of the cursor. If `dest` is file-like, it will be
    appended to or overwritten from the current position of the cursor.
    Otherwise, it will be truncated.

    `hook` is a function that accepts a line from `src` and returns the
    modified line to write into `dest`. The default value of
    :py:obj:`None` is equivalent to a pass-thru like ``lambda x: x``. A
    return value of :py:obj:`None` means to print nothing to the file.
    This is not the same as an empty string if ``strip_newlines=True``.

    If `strip_newlines` is :py:obj:`False` (the default), the input to
    `hook` will contain the trailing newline characters. Whether or not
    the output does is entirely up to the implementation, but one will
    not be automatically appended. If `strip_newlines` is
    :py:obj:`True`, the input to `hook` will not contain the trailing
    newline and one will be appended to the output if the input
    contained one.
    """
    with open_file(src, 'rt', encoding=encoding) as src_file, \
         open_file(dest, 'wt', encoding=encoding) as dest_file:
        while True:
            line = src_file.readline()
            if not line:
                break
            if strip_newlines and line[-1] == '\n':
                eol = line[-1]
                line = line[:-1]
            else:
                eol = ''
            if hook:
                line = hook(line)
            if line is not None:
                dest_file.write(line)
                dest_file.write(eol)


def add_system_path(*paths, append=True, var='PATH'):
    """
    Extends the :envvar:`PATH` environment variable with the specified
    sequence of additional elements.

    Elements are only added if they are not already present in the
    existing path. This function only does literal comparison and
    append. It does not account for environment variable expansion or
    anything like that.
    """
    env_path = environ.get(var, '').split(pathsep)

    add = env_path.append if append else partial(env_path.insert, 0)

    for path in paths:
        if path not in env_path:
            add(str(path))

    environ[var] = pathsep.join(filter(None, env_path))


class Tee:
    """
    An output stream that directs output to two different streams.

    This class provides a :py:meth:`write` and :py:meth:`flush` methods.
    Since it is intended to be used with :py:obj:`sys.stdout` and
    :py:obj:`sys.stderr`, it also provides an :py:meth:`isatty` method,
    which always returns :py:obj:`False`.

    .. py:attribute:: s1

       The first stream to write to in the tee.

    .. py:attribute:: s2

       The second stream to write to in the tee.

    No checking is done on the streams, e.g., to make sure that they are
    opened with the same mode, etc.

    .. todo:: Add the proper mixins/ABCs from io package.
    """
    def __init__(self, stream1, stream2):
        """
        Initializes a tee to the specified streams.
        """
        self.s1 = stream1
        self.s2 = stream2

    def __repr__(self):
        return '{type}(s1={self.s1!r}, s2={self.s2!r})'.format(
            type=type(self).__qualname__, self=self
        )

    def write(self, string):
        """
        Write the output to both teed streams.

        This method does not return anything.
        """
        self.s1.write(string)
        self.s2.write(string)

    def flush(self):
        """
        Attempt to flush both teed streams.

        Streams are only flushed if they have a callable ``flush``
        method. Closed streams will not be flushed.
        """
        self._call_method(self.s1, 'flush')
        self._call_method(self.s2, 'flush')

    def isatty(self):
        """
        Always return :py:obj:`False` to indicate redirection.
        """
        return False

    def close(self):
        """
        Closes either of the underlying streams that is not a TTY.

        Streams with no callable ``isatty`` attribute are closed if they
        have a callable ``close`` attribute.
        """
        def close_not_tty(obj):
            if not self._call_method(obj, 'isatty'):
                self._call_method(obj, 'close')

        close_not_tty(self.s1)
        close_not_tty(self.s2)

    @staticmethod
    def _call_method(obj, name):
        """
        Checks if a (file) object has a named method and returns the
        result of calling it.

        If the attribute does not exist or is not :py:func:`callable`,
        return :py:obj:`None`. Methods are assumed to be no-arg.

        Methods are expected to raise a :py:exc:`ValueError` if the file
        is closed. The error will be ignored and the return value will
        be :py:obj:`None`.
        """
        meth = getattr(obj, name, None)
        if meth is None or not callable(meth):
            return None
        try:
            return meth()
        except ValueError:
            # Raised to indicate that file is already closed:
            # https://stackoverflow.com/a/11859306/2988730
            return None


class StdoutTee(Tee):
    """
    Tees output to :py:obj:`sys.stdout` and another stream.

    This class replaces :py:obj:`sys.stdout` if used as a context
    manager. It retains a reference to the original stream, which it
    replaces on exit.
    """
    def __init__(self, stream):
        """
        Initialize a tee with `stream` and :py:obj:`sys.stdout`.
        """
        super().__init__(stream, sys.stdout)

    def __enter__(self):
        """
        Replace :py:obj:`sys.stdout` with this object.

        Return this object.
        """
        sys.stdout = self
        return self

    def __exit__(self, *args, **kwargs):
        """
        Replace the current :py:obj:`sys.stdout` with the original and
        close the other stream.
        """
        sys.stdout = self.s2
        self.close()


class StderrTee(Tee):
    """
    Tees output to :py:obj:`sys.stderr` and another stream.

    This class replaces :py:obj:`sys.stderr` if used as a context
    manager. It retains a reference to the original stream, which it
    replaces on exit.
    """
    def __init__(self, stream):
        """
        Initialize a tee with `stream` and :py:obj:`sys.stderr`.
        """
        super().__init__(stream, sys.stderr)

    def __enter__(self):
        """
        Replace :py:obj:`sys.stderr` with this object.

        Return this object.
        """
        sys.stderr = self
        return self

    def __exit__(self, *args, **kwargs):
        """
        Replace the current :py:obj:`sys.stderr` with the original and
        close the other stream.
        """
        sys.stderr = self.s2
        self.close()


@contextmanager
def redirect_stream(from_stream, to_stream):
    """
    Similar to :py:func:`contextlib.redirect_stderr` and
    :py:func:`contextlib.redirect_stdout`, except that it works with
    OS-level file descriptors instead of :py:obj:`sys.stderr` and
    :py:obj:`sys.stdout`.

    While less portable, this context manager will correctly redirect
    output from C and C++ libraries. The only restrictions on
    `from_stream` and `to_stream` are that they must both have a valid
    `fileno`. This function ostensibly works on any non-WASI POSIX OS.
    """
    original = dup(from_stream.fileno())
    dup2(to_stream.fileno(), from_stream.fileno())
    try:
        yield
    finally:
        dup2(original, from_stream.fileno())
        close(original)


@contextmanager
def redirect_stderr(stream):
    """
    Similar to :py:func:`contextlib.redirect_stderr` except that it
    works with OS-level file descriptors instead of
    :py:obj:`sys.stdout`.

    While less portable than its namesake, this context manager will
    correctly redirect output from C and C++ libraries. The only
    restriction on `stream` is that it must have a valid `fileno` (as
    must :py:obj:`sys.stderr`). This function ostensibly works on any
    non-WASI POSIX OS.
    """
    with redirect_stream(sys.stderr, stream):
        yield


@contextmanager
def redirect_stdout(stream):
    """
    Similar to :py:func:`contextlib.redirect_stdout` except that it
    works with OS-level file descriptors instead of
    :py:obj:`sys.stdout`.

    While less portable than its namesake, this context manager will
    correctly redirect output from C and C++ libraries. The only
    restriction on `stream` is that it must have a valid `fileno` (as
    must :py:obj:`sys.stderr`). This function ostensibly works on any
    non-WASI POSIX OS.
    """
    with redirect_stream(sys.stdout, stream):
        yield


@contextmanager
def suppress_stderr():
    """
    Redirect :py:obj:`sys.stderr` to :py:obj:`os.devnull`.

    Unlike :py:func:`contextlib.redirect_stdout`, which operates
    directly on :py:obj:`sys.stdout`, this function operates on the
    underlying file descriptors. While it may be less portable, this
    context manager will correctly suppress output from C and C++
    libraries.This function ostensibly works on any non-WASI POSIX OS.
    """
    with open(devnull, "w") as sink, redirect_stream(sys.stderr, sink):
        yield


@contextmanager
def suppress_stdout():
    """
    Redirect :py:obj:`sys.stdout` to :py:obj:`os.devnull`.

    Unlike :py:func:`contextlib.redirect_stdout`, which operates
    directly on :py:obj:`sys.stdout`, this function operates on the
    underlying file descriptors. While it may be less portable, this
    context manager will correctly suppress output from C and C++
    libraries.This function ostensibly works on any non-WASI POSIX OS.
    """
    with open(devnull, "w") as sink, redirect_stream(sys.stdout, sink):
        yield


@contextmanager
def chdir_context(path, current=None):
    """
    A context manager that changes the current directory using
    :py:func:`os.chdir`.

    The `current` directory is reinstated once the manager exits.

    Parameters
    ----------
    path : path-like or file-descriptor
        The directory to temporarily change to. Any argument that is
        valid for :py:func:`os.chdir` is valid here.
    current : path-like or file-descriptor or None
        The directory to return to once the context manager exits. If
        omitted or :py:obj:`None`, the current working directory as
        returned by :py:func:`os.getcwd` is used. As with `path`, the
        argument must be valid for :py:func:`os.chdir`.
    """
    if current is None:
        current = getcwd()

    try:
        chdir(path)
        yield
    finally:
        chdir(current)
