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
Tools to help with threading.
"""


__all__ = ['Heartbeat']


from contextlib import contextmanager
from time import sleep
from threading import Thread


class Heartbeat(Thread):
    """
    A simple timer-like thread that emits a signal at fixed intervals.

    The thread can be stopped and paused using a context manager.
    """
    def __init__(self, emit, name='heartbeat', interval=1.0):
        """
        Construct a thread with the specified signal, name and interval.

        Parameters
        ----------
        emit : callable
            The no-arg callable to invoke to emit a signal.
        name : str, optional
            The name of the thread. The default is 'heartbeat'.
        interval : float, optional
            The interval from the end of one call to `emit` and the next
            invocation. Units are seconds. The default is 1.0.
        """
        super().__init__(name=name)
        self.running = False
        self.suspended = False
        self.emit = emit
        self.interval = float(interval)

    def start(self):
        """
        Start the thread.
        """
        self.running = True
        super().start()

    def stop(self):
        """
        Stop the heartbeat.

        The thread may not die until the current interval completes, but
        the signal will not be emitted again once this method is called.
        """
        self.running = False

    @contextmanager
    def suspend(self):
        """
        Context manager to temporarily suspend the heartbeat.

        Emission will stop when the manager enters, and resume on the
        next interval when it exits. Thread will die if an error occurs
        during suspension. Intervals are still timed while the thread is
        suspened.
        """
        self.suspended = True
        try:
            yield
        except:
            # Do not un-suspend on error: prevent last iteration from running
            self.running = False
            raise
        else:
            self.suspended = False

    def run(self):
        """
        Emit a signal immediately, and at somewhat regular intervals
        thereafter.
        """
        self.emit()
        while self.running:
            sleep(self.interval)
            if not self.suspended and self.running:
                self.emit()
