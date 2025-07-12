#!/usr/bin/env python3
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

# Author: Joseph Fox-Rabinovitz <jfoxrabinovitz at gmail dot com>
# Version: 13 Apr 2019: Initial Coding

"""
Utilities for working with FITS files, only available when the
``[scio]`` :ref:`extra <installation-extras>` is installed.

If `astropy`_ is not found at import time, this module will have a
:py:data:`fits_enabled` attribute, which will be :py:obj:`False`. If
`astropy`_ is found, on the other hand, :py:data:`fits_enabled` will
be :py:obj:`True`, and all the dependent functions and attributes of the
module will be present.

.. py:data:: fits_enabled

   A boolean value indicating whether the ``[scio]``
   :ref:`extra <installation-extras>` has been installed. If
   :py:obj:`False`, the API will be severely limited.


.. include:: /link-defs.rst 
"""

__all__ = ['fits_enabled']


import os, tempfile, warnings


try:
    from astropy.io import fits
except ImportError:
    from .. import _display_missing_extra
    _display_missing_extra('scio', 'astropy')
    fits_enabled = False
else:
    __all__.extend(['TempFITS'])
    fits_enabled = True


if fits_enabled:
    class TempFITS():
        """
        A context manager for storing the contents of a numpy array to a
        temporary FITS file.

        If created successfuly, the file is deleted when the context
        manager exits.

        .. py:attribute:: filename

           The name of the temporary file, either passed in directly, or
           generated during initialization.

        .. py:attribute:: delete_on_close

           Indicates whether or not the underlying file will be deleted
           when the context manager exits. Default is :py:obj:`True`.

        .. py:attribute:: open_file

           Whether or not the context manager should return a file
           object opened for reading along with the filename when it
           enters. The default is to return only the filename.

        .. py:attribute:: file

           The file handle opened by when the context manager enters,
           if :py:attr:`open_file` is :py:obj:`True`. At all other
           times, this attribute is :py:obj:`None`.

        .. todo::

           Most of TempFITS can be factored out into a much more general
           base class.
        """
        def __init__(self, array, filename=None, *, open_file=True,
                     delete_on_close=True, **kwargs):
            """
            Dump the specified array to a file and record the file name.

            If `filename` is given, use it as-is and ignore all
            `kwargs`. Otherwise, pass the keyword arguments `suffix`,
            `prefix` and `dir` to :py:func:`tempfile.mkstemp` when
            creating the file. The `text` keyword may only be set to
            :py:obj:`False`. It will be ignored with a warning if
            :py:obj:`True` since FITS files are binary by their nature.

            The name of the file is stored in the :py:attr:`filename`
            attribute of this object. The named file can be closed and
            reopened at will, but keep in mind that it will be deleted
            when this context manager exits if `delete_on_close` is
            :py:obj:`True`.

            `open_file` determines if a file object open for reading is
            returned when the context manager is entered, in addition to
            the file name.
            """
            if kwargs.get('text'):
                warnings.warn('Illegal value True for "text" argument '
                              'to mkstemp for FITS files')
                kwargs['text'] = False

            if filename:
                self.filename = filename
                file = open(filename, 'wb')
            else:
                fd, self.filename = tempfile.mkstemp(**kwargs)
                file = os.fdopen(fd, 'wb')

            with file:
                fits.PrimaryHDU(array).writeto(file)

            self.delete_on_close = delete_on_close
            self.open_file = open_file
            self.file = None

        def __enter__(self):
            """
            Return the name of the file and optionally a file object
            open for reading.

            If :py:attr:`open_file` is :py:obj:`True`, a file handle
            opened for reading will be returned as a second output
            argument. The file pointer will be set to the beginning.
            """
            if self.openFile:
                self.file = open(self.filename, 'rb')
                return self.filename, self.file
            else:
                self.file = None
                return self.filename

        def __exit__(self, *exc_info):
            """
            Ensure that the file is closed regardless of any exceptions,
            and deleted if :py:attr:`delete_on_close` was chosen.

            *Any* closeable handle that is assigned to the
            :py:attr:`file` attribute will be closed, even if it was not
            the one that was opened originally, and regardless of
            :py:attr:`open_file`.
            """
            if self.file:
                self.file.close()
                self.file = None
            if self.delete_on_close:
                os.remove(self.filename)
