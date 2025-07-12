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
# Version: 10 Feb 2021: Initial Coding

"""
Timing, timer, time and suchlike tools.
"""


__all__ = ['Stopwatch', 'timestamp']


from collections import deque
from contextlib import AbstractContextManager
from datetime import datetime
from time import time


class _StopwatchPause(AbstractContextManager):
    """
    A context manager for measuring stopwatch pauses.
    """
    __slots__ = ('parent')

    def __init__(self, stopwatch):
        """
        Measures the duration of pauses in a running stopwatch.

        Parameters
        ----------
        stopwatch : Stopwatch
            The parent object.
        """
        self.parent = stopwatch

    def __exit__(self, *args):
        """
        Stops the pause and updates the parent :py:class:`Stopwatch`.
        """
        self.parent.unpause()
        return super().__exit__(*args)


class Stopwatch(AbstractContextManager):
    """
    Rough lightweight timer context manager.

    This is not intended to be used for precise benchmarking, but can
    give a good idea of how long operations in a `with` block take.

    The context manager can be reused as many times as necessary. When
    first created, it reports time relative to its creation time,
    unless specifically requested otherwise.

    .. py:attribute:: start

       The start time of the stopwatch, as a floating point timestamp
       from Epoch (see :py:func:`time.time`). This is valid regardless
       of whether the stopwatch is running or not.

    .. py:attribute:: end

       The end time of the stopwatch, as a floating point timestamp
       from Epoch (see :py:func:`time.time`). If the stopwatch is
       running, this is set to None. If it is stopped or paused, this
       attribute records the time of the stop or pause.

    .. py:attribute:: pauses

       A sequence containing ``(start, end)`` tuples for every pause
       triggered since the last restart. The last element may be a
       placeholder object if the stopwatch is paused. All tuple
       elements have units of seconds from Epoch (see
       :py:func:`time.time`).

    .. py:attribute:: pause_duration

       The sum of the durations of all the pauses, in seconds.

    This class is not thread safe.
    """
    __slots__ = ('start', 'end', 'pauses', 'pause_duration')

    def __init__(self, start=None):
        """
        Create a new stopwatch, starting from now.

        Parameters
        ----------
        start : float or None, optional
            The start timestamp, or now if None. The default is None.
        """
        # The container must be created before it is cleared
        self.pauses = deque()
        # This clears the pauses container and sets pause_duration
        self.restart()
        if start is not None:
            self.start = start

    def __enter__(self):
        """
        Restart the timer.

        See :py:meth:`restart`.
        """
        self.restart()
        return super().__enter__()

    def __exit__(self, *args):
        """
        Stops the timer.

        See :py:meth:`stop`.
        """
        self.stop()
        return super().__exit__(*args)

    def __str__(self):
        """
        Pretty-prints the duration of this stopwatch, with a label to
        indicate if it is running.

        Returns
        -------
        str :
            A string representation of the stopwatch duration.
        """
        df = self.duration
        di = int(df)
        s = 'Running' if self.end is None else 'Stopped'
        return f'{di // 3600:02d}:{(di // 60) % 60:02d}:{df % 60:0.2f} [{s}]'

    @property
    def duration(self):
        """
        The duration of the stopwatch timer, including any intervening
        pauses. If the stopwatch is running, this is the duration until
        now. If stopped, this is the duration between start and stop.
        """
        start = self.start + self.pause_duration
        end = time() if self.end is None else self.end
        return end - start

    def restart(self):
        """
        Clears the pause sequence and restarts the timer.
        """
        self.clear()
        self.end = None
        self.start = time()

    def pause(self):
        """
        Pause the stopwatch, if not already paused.

        This method returns a context manager. Entering the context
        manager does nothing, but exiting it unpauses this timer.

        Calling this method multiple times without unpausing will
        lead to potentially unexpected behavior. All context managers
        returned by this method unpause the stopwatch. That means, for
        example, that nesting context managed calls to :py:meth:`pause`
        will unpause when the innermost context manager exits, not the
        outermost.

        Returns
        -------
        A subsidiary context manager that can be used to automatically
        :py:meth:`unpause` when it exits.
        """
        if self.end is None:
            self.end = time()
        return _StopwatchPause(self)

    def unpause(self):
        """
        Unpause the timer, if it has been paused.

        :py:attr:`pause_duration` is updated and a new entry is
        appended to :py:attr:`pauses` if the timer was not running.
        """
        self._unstop()
        self.end = None

    def stop(self):
        """
        Stops the timer.

        Calling this method multiple times will update :py:attr:`end`
        and :py:attr:`pause_duration`, and append a new entry to the
        :py:attr:`pauses` sequence from the last stop/pause.
        """
        self.end = self._unstop()

    def clear(self):
        """
        Removes all pause records, including any current ones.

        Clearing the records will affect the reported duration, whether
        the stopwatch is running or not.
        """
        self.pauses.clear()
        self.pause_duration = 0.0

    def _unstop(self):
        """
        If :py:attr:`end` is not None, update :py:attr:`pauses` and
        :py:attr:`pause_duration`.

        Used by :py:attr:`stop` and :py:attr:`unpause` to update the
        timer.

        Returns
        -------
        end : float
            The current time (at the start of the method).
        """
        end = time()
        start = self.end
        if start is not None:
            self.pauses.append((start, end))
            self.pause_duration += end - start
        return end


def timestamp(t=None):
    """
    Return the current or other date and time in the format
    ``YYYYMMDD_HHMMSS``.

    Parameters
    ----------
    t : datetime.datetime or None
        The date to format. If `None`, use the result of
        :py:meth:`datetime.datetime.now`.

    Returns
    -------
    str
        The formatted date.
    """
    if t is None:
        t = datetime.now()
    return t.strftime('%Y%m%d_%H%M%S')
