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
Utilities for extending and configuring the Python XML framework.
"""

__all = ['SAXBase', 'SAXLoggable']


from xml.sax.handler import ContentHandler

from ..logs import MetaLoggableType


class SAXBase(ContentHandler):
    """
    An empty SAX parser with some convenience functionality built in.

    This class provides a reference to the locator. All of the actual SAX
    callback methods are currently no-ops.
    """
    def __init__(self):
        """
        Initialize the base classes and set the locator to `None`.
        """
        super().__init__()
        self.locator = None

    def setDocumentLocator(self, locator):
        """
        Set the locator used in error reporting.

        The locator can be accessed through the :py:meth:`locate`
        message-reformatting utility method.
        """
        self.locator = locator

    def _get_position(self):
        """
        Retrieve the position based on the currently configured locator.

        If there is no locator set, the position will be NaN.
        """
        if self.locator is None:
            return (float('nan'),) * 2
        return self.locator.getLineNumber(), self.locator.getColumnNumber()

    def locate(self, message, *args, short=False):
        """
        Convert a message and argument-list to a message with location
        information, and extends the argument list appropriately.

        Return a tuple containing two elements: the message and the
        argument list as a single tuple that can be expanded into the
        argument of any of the logging methods.

        The full version of the location string (default) includes the
        file name, the line number and the column. The short version
        only inculdes the line number and column.
        """
        if short:
            message += ' on line %d:%d'
            extra = self._get_position()
        else:
            message += ' in %s:%d:%d'
            extra = (self.locator.getSystemId(), *self._get_position())
        return (message, (*args, *extra))

    def short_locate(self, message, *args):
        """
        Identical to :py:meth:`locate`, except that the file name is not
        included in the updated message.
        """
        return (message + ' on line %d:%d', (*args, *self._get_position()))


class SAXLoggable(SAXBase, metaclass=MetaLoggableType):
    """
    A type of :py:class:`SAXBase` that provides logging in addition to
    location methods.
    """
    def log(self, level, msg, *args, **kwargs):
        """
        Append location information to a log message.

        This method allows an additional keyword argument `short` that
        determines whether or not the full file name will be present in
        the location. `short` is :py:obj:`True` by default, meaning that
        only the line and column number are reported.
        """
        short = kwargs.pop('short', 'True')
        msg, args = self.locate(msg, *args, short=short)
        self.logger.log(level, msg, *args, **kwargs)

    def setDocumentLocator(self, locator, level=None):
        """
        Set the locator used in error reporting and log it, with
        location.

        Logging is done using :py:meth:`log`. The locator will not be
        logged if `level` is :py:obj:`None`.
        """
        super().setDocumentLocator(locator)
        if level is not None:
            self.log(level, "Set document locator")
