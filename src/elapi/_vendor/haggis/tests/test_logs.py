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
# Version: 01 Nov 2022: Initial Coding

"""
Tests for the :py:mod:`haggis.logs` module.
"""


from contextlib import contextmanager
from io import StringIO
import logging
import sys
from warnings import catch_warnings

from pytest import fixture, raises

from ..logs import (
    KEEP, KEEP_WARN, OVERWRITE, OVERWRITE_WARN, RAISE,
    add_logging_level, reset_handlers, LogMaxFilter, MetaLoggableType
)


class LoggingTestBase(metaclass=MetaLoggableType):
    levelNames = {
        lvl: logging.getLevelName(lvl) for lvl in (
            logging.DEBUG, logging.INFO, logging.WARNING,
            logging.ERROR, logging.CRITICAL
        )
    }

    @fixture
    def reset_handler(self):
        return True

    @fixture
    def initial_level(self):
        return logging.DEBUG

    @fixture
    def formatter(self):
        return logging.Formatter('%(levelname)s %(message)s')

    @fixture(autouse=True)
    def log_setup(self, initial_level, reset_handler, formatter):
        self.stream = StringIO()
        self.handler = logging.StreamHandler(self.stream)
        if reset_handler:
            reset_handlers(self.handler, logger=self.logger,
                           level=initial_level, format=formatter,
                           filter_type=False)
        else:
            self.handler.setFormatter(formatter)
            self.handler.setLevel('NOTSET')
            self.logger.addHandler(self.handler)
        self.logger.setLevel(initial_level)


class TestAddLoggingLevel(LoggingTestBase):
    @contextmanager
    def remove_level(self, name, method=None):
        yield
        if method is None:
            method = name.lower()
        logging._acquireLock()
        try:
            level = getattr(logging, name)
            delattr(logging, name)
            delattr(logging, method)
            delattr(logging.getLoggerClass(), method)
            delattr(logging.LoggerAdapter, method)
            if hasattr(logging, '_levelToName') and \
                                level in logging._levelToName:
                del logging._levelToName[level]
            if hasattr(logging, '_nameToLevel') and \
                                name in logging._nameToLevel:
                del logging._nameToLevel[name]
        finally:
            logging._releaseLock()

    def test_basic(self):
        with self.remove_level('XDEBUG'):
            add_logging_level('XDEBUG', logging.DEBUG + 5)
            assert getattr(logging, 'XDEBUG') == logging.DEBUG + 5
            assert logging.getLevelName('XDEBUG') == logging.DEBUG + 5
            assert logging.getLevelName(logging.DEBUG + 5) == 'XDEBUG'
            assert hasattr(logging, 'xdebug')
            assert hasattr(logging.getLoggerClass(), 'xdebug')
            assert hasattr(logging.LoggerAdapter, 'xdebug')

    def test_keep(self):
        with catch_warnings(record=True) as w, self.remove_level('XDEBUG'):
            add_logging_level('XDEBUG', logging.DEBUG + 5, if_exists=KEEP)
            assert not w

            add_logging_level('XDEBUG', logging.DEBUG + 1, if_exists=KEEP)
            assert not w

            assert getattr(logging, 'XDEBUG') == logging.DEBUG + 5
            assert logging.getLevelName('XDEBUG') == logging.DEBUG + 5
            assert logging.getLevelName(logging.DEBUG + 5) == 'XDEBUG'
            assert hasattr(logging, 'xdebug')
            assert hasattr(logging.getLoggerClass(), 'xdebug')
            assert hasattr(logging.LoggerAdapter, 'xdebug')

    def test_keep_warn(self):
        with catch_warnings(record=True) as w, self.remove_level('XDEBUG'):
            add_logging_level('XDEBUG', logging.DEBUG + 5, if_exists=KEEP_WARN)
            assert not w

            add_logging_level('XDEBUG', logging.DEBUG + 1, if_exists=KEEP_WARN)
            assert len(w) == 1
            assert 'XDEBUG' in str(w[0].message)
            assert '2/5' in str(w[0].message)  # logging.XDEBUG and mapping

            add_logging_level('XDEBUG', logging.DEBUG + 5, if_exists=KEEP_WARN)
            assert len(w) == 1

            assert getattr(logging, 'XDEBUG') == logging.DEBUG + 5
            assert logging.getLevelName('XDEBUG') == logging.DEBUG + 5
            assert logging.getLevelName(logging.DEBUG + 5) == 'XDEBUG'
            assert hasattr(logging, 'xdebug')
            assert hasattr(logging.getLoggerClass(), 'xdebug')
            assert hasattr(logging.LoggerAdapter, 'xdebug')

    def test_overwrite(self):
        with catch_warnings(record=True) as w, self.remove_level('XDEBUG'):
            add_logging_level('XDEBUG', logging.DEBUG + 5, if_exists=OVERWRITE)
            assert not w

            add_logging_level('XDEBUG', logging.DEBUG + 1, if_exists=OVERWRITE)
            assert not w

            assert getattr(logging, 'XDEBUG') == logging.DEBUG + 1
            assert logging.getLevelName('XDEBUG') == logging.DEBUG + 1
            assert logging.getLevelName(logging.DEBUG + 5) == 'XDEBUG'
            assert hasattr(logging, 'xdebug')
            assert hasattr(logging.getLoggerClass(), 'xdebug')
            assert hasattr(logging.LoggerAdapter, 'xdebug')

    def test_overwrite_warn(self):
        with catch_warnings(record=True) as w, self.remove_level('XDEBUG'):
            add_logging_level('XDEBUG', logging.DEBUG + 5,
                              if_exists=OVERWRITE_WARN)
            assert not w

            add_logging_level('XDEBUG', logging.DEBUG + 1,
                              if_exists=OVERWRITE_WARN)
            assert len(w) == 1
            assert 'XDEBUG' in str(w[0].message)
            assert '2/5' in str(w[0].message)  # logging.XDEBUG and mapping

            add_logging_level('XDEBUG', logging.DEBUG + 1,
                              if_exists=OVERWRITE_WARN)
            assert len(w) == 1

            assert getattr(logging, 'XDEBUG') == logging.DEBUG + 1
            assert logging.getLevelName('XDEBUG') == logging.DEBUG + 1
            assert logging.getLevelName(logging.DEBUG + 5) == 'XDEBUG'
            assert hasattr(logging, 'xdebug')
            assert hasattr(logging.getLoggerClass(), 'xdebug')
            assert hasattr(logging.LoggerAdapter, 'xdebug')

    def test_raise(self):
        with catch_warnings(record=True) as w, self.remove_level('XDEBUG'):
            add_logging_level('XDEBUG', logging.DEBUG + 5, if_exists=RAISE)
            assert not w

            raises(AttributeError, add_logging_level, 'XDEBUG',
                   logging.DEBUG + 1, if_exists=RAISE)
            assert not w

            add_logging_level('XDEBUG', logging.DEBUG + 5, if_exists=RAISE)
            assert not w

            assert getattr(logging, 'XDEBUG') == logging.DEBUG + 5
            assert logging.getLevelName('XDEBUG') == logging.DEBUG + 5
            assert logging.getLevelName(logging.DEBUG + 5) == 'XDEBUG'
            assert hasattr(logging, 'xdebug')
            assert hasattr(logging.getLoggerClass(), 'xdebug')
            assert hasattr(logging.LoggerAdapter, 'xdebug')

    def test_logger(self):
        with self.remove_level('XDEBUG'):
            add_logging_level('XDEBUG', logging.DEBUG + 5, if_exists=RAISE)
            self.logger.xdebug('message1')
            self.logger.log(logging.XDEBUG, 'message2')
        self.handler.flush()
        assert self.stream.getvalue() == 'XDEBUG message1\nXDEBUG message2\n'

    def test_logger_adapter(self):
        with self.remove_level('XDEBUG'):
            add_logging_level('XDEBUG', logging.DEBUG + 5, if_exists=RAISE)
            adapter = logging.LoggerAdapter(self.logger, {})
            adapter.xdebug('message1')
            adapter.log(logging.XDEBUG, 'message2')
        self.handler.flush()
        assert self.stream.getvalue() == 'XDEBUG message1\nXDEBUG message2\n'

    def test_bad_name(self):
        raises(ValueError, add_logging_level, 'lowercase', 1)


class TestResetHandlers(LoggingTestBase):
    @fixture
    def reset_handler(self):
        return False

    def test_handler_none(self):
        raises(AttributeError, reset_handlers, None, logger=self.logger)

    def test_format(self):
        stream = StringIO()
        if sys.version_info >= (3, 8):
            format = logging.Formatter('XXX', validate=False)
        else:
            format = logging.Formatter('XXX')
        reset_handlers(logging.StreamHandler(stream), logger=self.logger,
                       format=format, filter_type=False)
        self.logger.debug('test')
        assert len(self.logger.handlers) == 1
        self.logger.handlers[0].flush()
        assert stream.getvalue() == 'XXX\n'

    def test_logger(self):
        logger = logging.getLogger(self.logger.name + '.a')

        for i in range(3):
            self.logger.addHandler(logging.NullHandler())

        reset_handlers(logging.NullHandler(), logger=logger, filter_type=False)

        assert len(self.logger.handlers) >= 3
        assert len(logger.handlers) == 1

    def test_level(self):
        reset_handlers(logging.NullHandler(), logger=self.logger,
                       level='WARNING', filter_type=False)
        assert len(self.logger.handlers) == 1
        assert self.logger.handlers[0].level == logging.WARNING

    def test_remove_hook(self):
        for i in range(3):
            self.logger.addHandler(logging.NullHandler())

        def remove_hook(handler):
            nonlocal remove_count
            remove_count += 1

        intial_count = len(self.logger.handlers)
        remove_count = 0

        reset_handlers(logging.NullHandler(), logger=self.logger,
                       remove_hook=remove_hook, filter_type=False)

        assert intial_count >= 3
        assert remove_count == intial_count

    def test_bad_filter_type(self):
        raises(TypeError, reset_handlers, logging.NullHandler(),
               filter_type='a')
        raises(TypeError, reset_handlers, logging.NullHandler(),
               filter_type=logging.StreamHandler)

    def test_type_filter_type(self):
        self.logger.handlers[:] = []
        for i in range(3):
            self.logger.addHandler(logging.StreamHandler(StringIO()))
            self.logger.addHandler(logging.NullHandler())
        assert len(self.logger.handlers) == 6

        reset_handlers(logging.NullHandler(), logger=self.logger)
        assert len(self.logger.handlers) == 4
        assert sum(isinstance(h, logging.NullHandler)
                   for h in self.logger.handlers) == 1
        assert sum(isinstance(h, logging.StreamHandler)
                   for h in self.logger.handlers) == 3

        reset_handlers(logging.NullHandler(), logger=self.logger,
                       filter_type=logging.Handler)
        assert len(self.logger.handlers) == 1
        assert isinstance(self.logger.handlers[0], logging.NullHandler)

    def test_true_filter_type(self):
        self.logger.handlers[:] = []
        for i in range(3):
            self.logger.addHandler(logging.StreamHandler(StringIO()))
            self.logger.addHandler(logging.NullHandler())
        assert len(self.logger.handlers) == 6

        reset_handlers(logging.NullHandler(), logger=self.logger,
                       filter_type=True)
        assert len(self.logger.handlers) == 4
        assert sum(isinstance(h, logging.NullHandler)
                   for h in self.logger.handlers) == 1
        assert sum(isinstance(h, logging.StreamHandler)
                   for h in self.logger.handlers) == 3

    def test_false_filter_type(self):
        self.logger.handlers[:] = []
        for i in range(3):
            self.logger.addHandler(logging.StreamHandler(StringIO()))
            self.logger.addHandler(logging.NullHandler())
        assert len(self.logger.handlers) == 6

        reset_handlers(logging.NullHandler(), logger=self.logger,
                       filter_type=False)
        assert len(self.logger.handlers) == 1
        assert isinstance(self.logger.handlers[0], logging.NullHandler)

    def test_filter_hook_no_type(self):
        self.logger.handlers[:] = []
        for i in range(3):
            self.logger.addHandler(logging.StreamHandler(StringIO()))
            self.logger.addHandler(logging.NullHandler())
        assert len(self.logger.handlers) == 6

        reset_handlers(logging.NullHandler(), logger=self.logger,
                       filter_hook=lambda h: True)
        assert len(self.logger.handlers) == 1
        assert isinstance(self.logger.handlers[0], logging.NullHandler)

    def test_filter_hook(self):
        self.logger.handlers[:] = []
        for i in range(6):
            htype = type('Handler{}'.format(i), (logging.Handler,), {})
            handler = htype(level=10 * i)
            self.logger.addHandler(handler)
        assert len(self.logger.handlers) == 6

        reset_handlers(logging.NullHandler(), logger=self.logger,
                       filter_hook=lambda h: h.level < 30)
        assert len(self.logger.handlers) == 4
        assert sum(isinstance(h, logging.NullHandler)
                   for h in self.logger.handlers) == 1

    def test_filter_hook_and_type(self):
        self.logger.handlers[:] = []
        for i in range(6):
            htype = type('Handler{}'.format(i), (logging.Handler,), {})
            handler = htype(level=10 * i)
            self.logger.addHandler(handler)
        assert len(self.logger.handlers) == 6

        reset_handlers(logging.NullHandler(), logger=self.logger,
                       filter_hook=lambda h: h.level < 30,
                       filter_type=logging.NullHandler)
        assert len(self.logger.handlers) == 7
        assert sum(isinstance(h, logging.NullHandler)
                   for h in self.logger.handlers) == 1

    def test_bad_filter_hook(self):
        raises(TypeError, reset_handlers, logger=self.logger, filter_hook='a')


class TestLogMaxFilter(LoggingTestBase):
    @fixture
    def reset_handler(self):
        return False

    @contextmanager
    def temp_log_max_filter(self, obj, *args, **kwargs):
        filter = LogMaxFilter(*args, **kwargs)
        obj.addFilter(filter)
        yield
        obj.removeFilter(filter)
        self.handler.flush()

    def test_inclusive_logger(self):
        with self.temp_log_max_filter(self.logger, 'WARNING', inclusive=True):
            for value, name in self.levelNames.items():
                self.logger.log(value, name)

        text = self.stream.getvalue()
        for value, name in self.levelNames.items():
            if value >= logging.WARNING:
                assert name not in text
            else:
                assert ' '.join((name, name)) in text

    def test_exclusive_logger(self):
        with self.temp_log_max_filter(self.logger, logging.WARNING,
                                      inclusive=False):
            for value, name in self.levelNames.items():
                self.logger.log(value, name)

        text = self.stream.getvalue()
        for value, name in self.levelNames.items():
            if value > logging.WARNING:
                assert name not in text
            else:
                assert ' '.join((name, name)) in text

    def test_inclusive_handler(self):
        with self.temp_log_max_filter(self.handler, logging.WARNING,
                                      inclusive=True):
            for value, name in self.levelNames.items():
                self.logger.log(value, name)

        text = self.stream.getvalue()
        for value, name in self.levelNames.items():
            if value >= logging.WARNING:
                assert name not in text
            else:
                assert ' '.join((name, name)) in text

    def test_exclusive_handler(self):
        with self.temp_log_max_filter(self.handler, 'WARNING',
                                      inclusive=False):
            for value, name in self.levelNames.items():
                self.logger.log(value, name)

        text = self.stream.getvalue()
        for value, name in self.levelNames.items():
            if value > logging.WARNING:
                assert name not in text
            else:
                assert ' '.join((name, name)) in text

        self.handler.removeFilter(filter)


    def test_custom_level(self):
        with self.temp_log_max_filter(self.logger, logging.WARNING + 5,
                                      inclusive=False):
            for value, name in self.levelNames.items():
                self.logger.log(value, name)

        text = self.stream.getvalue()
        for value, name in self.levelNames.items():
            if value > logging.WARNING:
                assert name not in text
            else:
                assert ' '.join((name, name)) in text

    def test_bad_level(self):
        raises(TypeError, LogMaxFilter, '_NOTALEVEL32', inclusive=True)
        raises(TypeError, LogMaxFilter, '_NOTALEVEL32', inclusive=False)


class TestMetaLoggableType:
    def test_regular(self):
        class Test(metaclass=MetaLoggableType):
            namespace = 'xxx'

        expected_name = Test.__module__ + '.' + Test.__qualname__

        assert not hasattr(Test, '__namespace__')
        assert isinstance(Test.logger, logging.Logger)
        assert Test.logger.name == expected_name
        assert logging.getLogger(expected_name) is Test.logger

    def test_namespace(self):
        class Test(metaclass=MetaLoggableType):
            __namespace__ = 'xxx'

        expected_name = Test.__namespace__ + '.' + Test.__module__ + '.' + Test.__qualname__

        assert hasattr(Test, '__namespace__')
        assert isinstance(Test.logger, logging.Logger)
        assert Test.logger.name == expected_name
        assert logging.getLogger(expected_name) is Test.logger

    def test_builtin(self):
        """ Verify that builtins play nicely with the metaclass. """
        class Test(list, metaclass=MetaLoggableType):
            __namespace__ = 'xyz'

        expected_name = Test.__namespace__ + '.' + Test.__module__ + '.' + Test.__qualname__

        assert hasattr(Test, '__namespace__')
        assert isinstance(Test.logger, logging.Logger)
        assert Test.logger.name == expected_name
        assert logging.getLogger(expected_name) is Test.logger
