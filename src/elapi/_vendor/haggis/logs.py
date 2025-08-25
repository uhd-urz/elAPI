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
Utilities for extending and configuring the logging framework.

This module is called ``logs`` instead of ``logging`` to avoid conflicts
with the builtin module. Since this module is a helper, it is expected
to be imported alongside the builtin module.
"""

__all__ = [
    'KEEP', 'KEEP_WARN', 'OVERWRITE', 'OVERWRITE_WARN', 'RAISE',
    'add_logging_level', 'add_trace_level', 'configure_logger',
    'reset_handlers',
    'LogMaxFilter', 'MetaLoggableType', 'ReturnableStreamHandler',
]


import abc
import logging
import sys
import warnings

from . import Sentinel


#: Default format string for the root logger. This string is set up by
#: the :py:func:`configure_logger` method.
_log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

#: When adding a new logging level, with :py:func:`add_logging_level`,
#: silently keep the old level in case of conflict.
KEEP = 'keep'


#: When adding a new logging level, with :py:func:`add_logging_level`,
#: keep the old level in case of conflict, and issue a warning.
KEEP_WARN = 'keep-warn'


#: When adding a new logging level, with :py:func:`add_logging_level`,
#: silently overwrite any existing level in case of conflict.
OVERWRITE = 'overwrite'


#: When adding a new logging level, with :py:func:`add_logging_level`,
#: overwrite any existing level in case of conflict, and issue a
#: warning.
OVERWRITE_WARN = 'overwrite-warn'


#: When adding a new logging level, with :py:func:`add_logging_level`,
#: raise an error in case of conflict.
RAISE = 'raise'


#: If used for `log_stderr` or `log_stdout` arguments of
#: :py:func:`configure_logger`, the corresponding stream output will
#: be handled by a :py:class:`ReturnableStreamHandler`.
RETURNABLE = 'returnable'


class MetaLoggableType(abc.ABCMeta):
    """
    A metaclass for assigning a logger with a properly named channel to
    classes.

    The logger channel will be the fully qualified name of the class
    including package and module prefixes.

    .. py:attribute:: __namespace__

       If this attribute is found in the class definition, it will be
       prefixed to the qualified name (with a dot).

    .. py:attribute:: logger

       This attribute is assigned to all new classes based on the name
       and possibly :py:attr:`__namespace__`.
    """

    def __init__(cls, name, bases, dct):
        """
        Intialize a newly created class with a :py:attr:`logger`
        attribute.

        If a `__namespace__` attribute is found in the class, its contents is
        prefixed to the logger name.
        """
        name = cls.__module__ + '.' + cls.__qualname__
        if '__namespace__' in dct:
            name = dct['__namespace__'] + '.' + name
        cls.logger = logging.getLogger(name)
        dct['logger'] = cls.logger
        return super().__init__(name, bases, dct)


def add_logging_level(level_name, level_num, method_name=None,
                      if_exists=KEEP, *, exc_info=False, stack_info=False):
    """
    Comprehensively add a new logging level to the :py:mod:`logging`
    module and the currently configured logging class.

    The `if_exists` parameter determines the behavior if the level
    name is already an attribute of the :py:mod:`logging` module or if
    the method name is already present, unless the attributes are
    configured to the exact values requested. Partial registration is
    considered a conflict. Even a complete registration will be
    overwritten if ``if_exists in (OVERWRITE, OVERWRITE_WARN)`` (without
    a warning of course).

    This function also accepts alternate default values for the keyword
    arguments ``exc_info`` and ``stack_info`` that are optional for
    every logging method. Setting alternate defaults allows levels for
    which exceptions or stacks are always logged.

    Parameters
    ----------
    level_name : str
        Becomes an attribute of the :py:mod:`logging` module with the
        value ``level_num``.
    level_num : int
        The numerical value of the new level.
    method_name : str
        The name of the convenience method for both :py:mod:`logging`
        itself and the class returned by
        :py:func:`logging.getLoggerClass` (usually just
        :py:class:`logging.Logger`). If ``method_name`` is not
        specified, ``level_name.lower()`` is used instead.
    if_exists : {KEEP, KEEP_WARN, OVERWRITE, OVERWRITE_WARN, RAISE}
        What to do if a level with `level_name` appears to already be
        registered in the :py:mod:`logging` module:

        :py:const:`KEEP`
            Silently keep the old level as-is.
        :py:const:`KEEP_WARN`
            Keep the old level around and issue a warning.
        :py:const:`OVERWRITE`
            Silently overwrite the old level.
        :py:const:`OVERWRITE_WARN`
            Overwrite the old level and issue a warning.
        :py:const:`RAISE`
            Raise an error.

        The default is :py:const:`KEEP_WARN`.
    exc_info : bool
        Default value for the ``exc_info`` parameter of the new method.
    stack_info : bool
        Default value for the ``stack_info`` parameter of the new
        method.

    Examples
    --------
    >>> add_logging_level('TRACE', logging.DEBUG - 5)
    >>> logging.getLogger(__name__).setLevel("TRACE")
    >>> logging.getLogger(__name__).trace('that worked')
    >>> logging.trace('so did this')
    >>> logging.TRACE
    5

    >>> add_logging_level('XTRACE', 2, exc_info=True)
    >>> logging.getLogger(__name__).setLevel(logging.XTRACE)
    >>> try:
    >>>     1 / 0
    >>> except:
    >>>     # This line will log the exception
    >>>     logging.getLogger(__name__).xtrace('that failed')
    >>>     # This one will not
    >>>     logging.xtrace('so did this', exc_info=False)

    The ``TRACE`` level can be added using :py:func:`add_trace_level`.

    Note
    ----
    Before adding new levels, please see the cautionary note here:
    https://docs.python.org/3/howto/logging.html#custom-levels.
    """
    # This method was inspired by the answers to Stack Overflow post
    # http://stackoverflow.com/q/2183233/2988730, especially
    # http://stackoverflow.com/a/13638084/2988730
    def for_logger_adapter(self, msg, *args, **kwargs):
        kwargs.setdefault('exc_info', exc_info)
        kwargs.setdefault('stack_info', stack_info)
        kwargs.setdefault('stacklevel', 2)
        self.log(level_num, msg, *args, **kwargs)

    def for_logger_class(self, msg, *args, **kwargs):
        if self.isEnabledFor(level_num):
            kwargs.setdefault('exc_info', exc_info)
            kwargs.setdefault('stack_info', stack_info)
            kwargs.setdefault('stacklevel', 2)
            self._log(level_num, msg, args, **kwargs)

    def for_logging_module(*args, **kwargs):
        kwargs.setdefault('exc_info', exc_info)
        kwargs.setdefault('stack_info', stack_info)
        kwargs.setdefault('stacklevel', 2)
        logging.log(level_num, *args, **kwargs)

    if not method_name:
        method_name = level_name.lower()
    if method_name == level_name:
        raise ValueError('Method name must differ from level name')

    # The number of items required for a full registration is 5
    items_found = 0
    # Items that are found complete but are not expected values
    items_conflict = 0

    def check_conflict(conflict, message):
        if conflict and if_exists == RAISE:
            raise AttributeError(message)
        return conflict

    def check_func_conflict(func, name, original_name, is_func, target):
        conflict = not (
            callable(func) and
            getattr(func, '_original_name', None) == original_name and
            getattr(func, '_exc_info', None) == exc_info and
            getattr(func, '_stack_info', None) == stack_info
        )
        return check_conflict(
            conflict, '{} {!r} already defined in {}'.format(
                "Function" if is_func else "Method", name, target
            )
        )
        return conflict

    # Lock because logger class and level name are queried and set
    logging._acquireLock()
    try:
        registered_num = logging.getLevelName(level_name)
        logger_class = logging.getLoggerClass()
        logger_adapter = logging.LoggerAdapter

        if registered_num != 'Level ' + level_name:
            items_found += 1
            items_conflict += check_conflict(
                registered_num != level_num, 'Level {!r} already registered '
                'in logging module'.format(level_name)
            )

        current_level = getattr(logging, level_name, Sentinel)
        if current_level is not Sentinel:
            items_found += 1
            items_conflict += check_conflict(
                current_level != level_num, 'Level {!r} already defined '
                'in logging module'.format(level_name)
            )

        logging_func = getattr(logging, method_name, Sentinel)
        if logging_func is not Sentinel:
            items_found += 1
            items_conflict += check_func_conflict(
                logging_func, method_name, for_logging_module.__name__,
                True, 'logging module'
            )

        logger_method = getattr(logger_class, method_name, Sentinel)
        if logger_method is not Sentinel:
            items_found += 1
            items_conflict += check_func_conflict(
                logger_method, method_name, for_logger_class.__name__,
                False, 'logger class'
            )

        adapter_method = getattr(logger_adapter, method_name, Sentinel)
        if adapter_method is not Sentinel:
            items_found += 1
            items_conflict += check_func_conflict(
                adapter_method, method_name, for_logger_adapter.__name__,
                False, 'logger adapter'
            )

        if items_found > 0:
            # items_found >= items_conflict always
            if (items_conflict or items_found < 5) and \
                    if_exists in (KEEP_WARN, OVERWRITE_WARN):
                action = 'Keeping' if if_exists == KEEP_WARN else 'Overwriting'
                if items_conflict:
                    problem = 'has conflicting definition'
                    items = items_conflict
                else:
                    problem = 'is partially configured'
                    items = items_found
                warnings.warn(
                    'Logging level {!r} {} already ({}/5 items): {}'.format(
                        level_name, problem, items, action)
                )

            if if_exists in (KEEP, KEEP_WARN):
                return

        # Make sure the method names are set to sensible values, but
        # preserve the names of the old methods for future verification.
        def label_func(func):
            func._original_name = func.__name__
            func.__name__ = method_name
            func._exc_info = exc_info
            func._stack_info = stack_info
        label_func(for_logging_module)
        label_func(for_logger_class)
        label_func(for_logger_adapter)

        # Actually add the new level
        logging.addLevelName(level_num, level_name)
        setattr(logging, level_name, level_num)
        setattr(logging, method_name, for_logging_module)
        setattr(logger_class, method_name, for_logger_class)
        setattr(logger_adapter, method_name, for_logger_adapter)
    finally:
        logging._releaseLock()


def add_trace_level(if_exists=KEEP_WARN):
    """
    Add a new ``TRACE`` level to the :py:mod:`logging` module.

    The numerical trace level is ``5`` lower than
    :py:data:`~logging.DEBUG`. It does not log stack or exception
    information by default. A ``trace`` method will be added to the
    :py:mod:`logging` module, to the current default
    :py:class:`~logging.Logger` class, and to the
    :py:class:`~logging.LoggerAdapter` class.
    """
    add_logging_level('TRACE', logging.DEBUG - 5, 'trace', if_exists)


def add_detail_level(if_exists=KEEP_WARN):
    """
    Add a new ``DETAIL`` level to the :py:mod:`logging` module.

    The numerical trace level is ``5`` higher than
    :py:data:`~logging.DEBUG`. It does not log stack or exception
    information by default. A ``detail`` method will be added to the
    :py:mod:`logging` module, to the current default
    :py:class:`~logging.Logger` class, and to the
    :py:class:`~logging.LoggerAdapter` class.
    """
    add_logging_level('DETAIL', logging.DEBUG + 5, 'detail', if_exists)


def LogMaxFilter(level, inclusive=True):
    """
    Create a level-based filter that caps the maximum allowed log level.

    Levels can be compared either exclusively or inclusively to the
    threshold.

    Parameters
    ----------
    level : int
        The cutoff level: only messages below this will be passed
        through.
    inclusive : bool
        If True, messages at level will be cut off. Otherwise, only
        messages strictly more severe than `level` will be cut off.

    Return
    ------
    filter :
        A callable filter that operates on log records.

    Notes
    -----
    This function returns a callable rather than an object with a
    ``filter`` method, so it is not compatible with `logging` before
    Python 3.2.
    """
    if not isinstance(level, int):
        level = logging.getLevelName(level)
    if not isinstance(level, int):
        raise TypeError('Numerical level or '
                        'level that maps to number required')
    comparator = level.__gt__ if inclusive else level.__ge__

    def filter(log_record):
        return comparator(log_record.levelno)

    return filter


class ReturnableStreamHandler(logging.StreamHandler):
    """
    Almost a normal stream handler, except that if a log record ends
    with `\r`, it does not insert a newline.

    Make sure to log something with a newline after overwriting prior
    outputs.

    May produce unexpected results in multiprocess scenario.
    """
    def __init__(self, *args, carriage_return='\r', **kwargs):
        super().__init__(*args, **kwargs)
        self.carriage_return = carriage_return
        self._last_line_length = 0

    def emit(self, record):
        """
        Emit a record.

        If a formatter is specified, it is used to format the record.
        The record is then written to the stream with a trailing
        newline. If exception information is present, it is formatted
        using `traceback.print_exception` and appended to the stream.
        If the stream has an 'encoding' attribute, it is used to
        determine how to do the output to the stream.
        """
        # Record value
        last_line_length = self._last_line_length

        try:
            msg = self.format(record)
            if msg.endswith(self.carriage_return):
                msg = msg.rstrip(self.carriage_return)
                terminator = self.carriage_return
                self._last_line_length = len(msg)
            else:
                terminator = self.terminator
                self._last_line_length = 0
            padding = ' '  * max(0, last_line_length - len(msg))

            self.stream.write(msg + padding + terminator)
            self.flush()
        except RecursionError:
            raise
        except Exception:
            self.handleError(record)


def _get_formatter(format=None):
    """
    Retrieve a consistent :py:class:`~logging.Formatter` object based
    on the input format.

    If `format` is already a :py:class:`~logging.Formatter`, return it
    as-is. If :py:obj:`None`, use a default format string. Otherwise, it
    is expected to be a string that initializes a proper
    :py:class:`~logging.Formatter` instance.
    """
    if isinstance(format, logging.Formatter):
        return format
    if format is None:
        format = _log_format
    return logging.Formatter(format)


def configure_logger(log_file=None, file_level='NOTSET',
                     log_stderr=True, stderr_level='WARNING',
                     log_stdout=False, stdout_level='INFO',
                     format_string=None, trace_warnings=True):
    """
    Set up the root logger based on the input parameters.

    A ``TRACE`` level is added to the :py:mod:`logging` module. The
    system-level automatic exception handler is set up to log uncaught
    errors. Warnings will always be captured by the logger, with
    optional tracebacks being logged by default.

    Parameters
    ----------
    log_file : None or str
        If not :py:obj:`None`, messages with level greater than or equal
        to `file_level` will go to the specified file.
    file_level : str
        The name of the minimum logging level that will be written to
        the file log if `log_file` is set. Defaults to ``'NOTSET'``.
        Case insensitive.
    log_stderr : bool or RETURNABLE
        If :py:obj:`True` or :py:obj:`RETURNABLE`, messages with level
        greater than or equal to `stderr_level` will be output to
        standard error. Defaults to :py:obj:`True`. The string
        :py:obj:`RETURNABLE` will use a
        :py:class:`ReturnableStreamHandler` to output messages.
    stderr_level : str
        The name of the minimum logging level that will be output to
        standard error if `log_stderr` is set. Defaults to
        ``'WARNING'``.
    log_stdout : bool or RETURNABLE
        If :py:obj:`True` or :py:obj:`RETURNABLE`, messages with level
        greater than or equal to `stdout_level` will be output to
        standard output. Defaults to :py:obj:`False`. The string
        :py:obj:`RETURNABLE` will use a
        :py:class:`ReturnableStreamHandler` to output messages. If
        `log_stderr` is set as well, only levels strictly less than
        `stderr_level` will be logged to standard output.
    stdout_level : str
        The name of the minimum logging level that will be output to
        standard error if `log_stdout` is set. Defaults to ``'INFO'``.
    format_string : str
        The log format. A missing (:py:obj:`None`) `format_string`
        defaults to
        ``'%(asctime)s - %(name)s - %(levelname)s - %(message)s'``. 
    trace_warnings : bool
        Whether or not to print tracebacks for actual warnings (not log
        entries with a warning level) caught by the Python global
        warning logger. Defaults to :py:obj:`True`. Custom
        :py:meth:`~logging.Logger.warning` methods are hooked into the
        logger for ``"py.warnings"``.
    """
    add_trace_level()

    # System-level logging hook courtesy of Stack Overflow post
    # http://stackoverflow.com/a/16993115/2988730
    def exception_handler(*args):
        """
        An exception hook that is meant to replace the default
        :py:func:`sys.excepthook`. Logs all uncaught exceptions to the
        root logger except for :py:exc:`KeyboardInterrupt`, which is
        passed directly to the default system hook.

        An additional hook can be called after logging the exception
        """
        if isinstance(args[0], KeyboardInterrupt):
            sys.__excepthook__(*args)
        else:
            root.critical("Uncaught exception", exc_info=args)

    sys.excepthook = exception_handler

    if trace_warnings:
        def warning_logger(self, msg, *args, **kwargs):
            """
            A replacement for the :py:meth:`~logging.Logger.warning`
            method that is set for the ``"py.warnings"`` logger to show
            a stack trace for logged warnings. Note that warnings logged
            explicitly with ``logger.log(logging.WARNING, ...)`` will
            not pass through this handler.
            """
            if self.isEnabledFor(logging.WARNING):
                kwargs.setdefault('stack_info', True)
                self._log(logging.WARNING, msg, args, **kwargs)

        logger = logging.getLogger("py.warnings")

        # Bind methods according to http://stackoverflow.com/a/1015405/2988730
        logger.warning = warning_logger.__get__(logger, type(logger))
        logger.warn = logger.warning  # For good measure

    logging.captureWarnings(True)

    # Remaining logger setup courtesy of Stack Overflow post
    # http://stackoverflow.com/a/24978464/2988730
    formatter = _get_formatter(format_string)

    root = logging.getLogger()
    # Apparently, stdout won't show up without this...
    root.setLevel(logging.NOTSET)

    if log_file:
        reset_handlers(logging.FileHandler(log_file, mode='w'),
                       level=file_level, format=formatter, logger=root)
    if log_stderr == RETURNABLE:
        stderr_handler_cls = ReturnableStreamHandler
        log_stderr = True
    else:
        stderr_handler_cls = logging.StreamHandler

    if log_stderr:
        reset_handlers(stderr_handler_cls(sys.stderr), level=stderr_level,
                       format=formatter, logger=root, filter_type=True,
                       filter_hook=lambda h: h.stream == sys.stderr)

    if log_stdout == RETURNABLE:
        stdout_handler_cls = ReturnableStreamHandler
        log_stdout = True
    else:
        stdout_handler_cls = logging.StreamHandler

    if log_stdout:
        stdout_handler = stdout_handler_cls(sys.stdout)
        reset_handlers(stdout_handler, level=stdout_level, format=formatter,
                       logger=root, filter_type=True,
                       filter_hook=lambda h: h.stream == sys.stdout)
        if log_stderr:
            stdout_handler.addFilter(LogMaxFilter(
                    logging.getLevelName(stderr_level), False))


def reset_handlers(handler, level='NOTSET', format=None, logger=None,
                   filter_type=None, filter_hook=None, remove_hook=None):
    """
    Remove all handlers of a given class from `logger` (root by
    default), and replaces them with `handler`.

    If a handler that is being removed has a ``close`` method, it will
    be called, unless `remove_hook` is explicitly set.

    If both `filter_type` and `filter_hook` are set, both conditions
    must be met in order for a handler to be removed.

    Parameters
    ----------
    handler : logging.Handler
        The new handler to place in the list.
    level : str
        The case insensitive name of the minimum logging level to
        set for `handler`. Defaults to ``'NOTSET'``. This will not
        affect the level set for the logger.
    format : None or str or logging.Formatter
        Format for the log output strings.
    logger : None or logging.Logger
        The logger to set the handler for. Defaults to the root logger.
        Neither child nor ancestor loggers will be affected by this
        operation.
    filter_type : None, bool or type
        The type of objects to remove from the current list of handlers.
        If a superclass of `handler`, it will be used as the filter
        instead of ``type(handler)``. Any other type will raise an error.
        If :py:obj:`None`, then filtering by type will be done only if
        `filter_hook` is not set. A :py:class:`bool` explicitly sets
        filtering by ``type(handler)`` on and off regardless of
        `filter_hook`.
    filter_hook : None or callable
        A function that accepts a :py:class:`~logging.Handler` and
        returns a :py:class:`bool`. :py:obj:`True` indicates that an
        object should be removed from the list of handlers.
    remove_hook : None or callable
        A function that accepts a :py:class:`~logging.Handler` and
        performs some additional action such as closing it. The default
        behavior is to invoke ``close()`` on all handlers that are being
        removed if they have that method.
    """
    if filter_type is None:
        if filter_hook is None:
            filter_type = type(handler)
    elif filter_type is True:
        filter_type = type(handler)
    elif filter_type is False:
        filter_type = None
    else:
        if not isinstance(handler, filter_type):
            raise TypeError('{} is not a subclass of {}'.format(
                type(handler), filter_type))

    if filter_hook is None:
        if filter_type is None:
            def filter_func(h):
                return True
        else:
            def filter_func(h):
                return isinstance(h, filter_type)
    else:
        if filter_type is None:
            filter_func = filter_hook
        else:
            def filter_func(h):
                return isinstance(h, filter_type) and filter_hook(h)

    if remove_hook is None:
        def remove_hook(h):
            if hasattr(h, 'close') and callable(h.close):
                h.close()

    logging._acquireLock()
    try:
        if logger is None:
            logger = logging.getLogger()

        for h in list(logger.handlers):
            if filter_func(h):
                remove_hook(h)
                logger.removeHandler(h)

        handler.setLevel(logging.getLevelName(level))
        handler.setFormatter(_get_formatter(format))
        logger.addHandler(handler)
    finally:
        logging._releaseLock()
