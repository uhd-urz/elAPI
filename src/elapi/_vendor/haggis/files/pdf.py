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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# Author: Joseph Fox-Rabinovitz <jfoxrabinovitz at gmail dot com>
# Version: 13 Apr 2019: Initial Coding

"""
Conversion utilities for PDF files to other formats.

This module relies on the ``[pdf]`` :ref:`extra <installation-extras>`,
which implies external programs. As such, this module may be quite
OS-sensitive. Specifically, it requires the programs :program:`pdftoppm`
and `ImageMagick`_\ 's :program:`convert`.

A small import-guarded block is provided to demo
:py:func:`pdf_to_image`.


.. include:: /link-defs.rst
"""

__all__ = ['pdftoppm_exe', 'convert_exe', 'pdf_to_image']


import subprocess, io


#: The name of the :program:`pdftoppm` executable. Either a full path,
#: or a program that the shell can find on the :envvar:`PATH` is
#: necessary.
pdftoppm_exe = 'pdftoppm'


#: The name of the `ImageMagick`_ :program:`convert` executable. Either
#: a full path, or a program that the shell can find on the
#: :envvar:`PATH` is necessary.
convert_exe = 'convert'


def pdf_to_image(input_path, output_path, format=None):
    """
    Convert a PDF document into an image file.

    This function uses the :py:mod:`subprocess` module to operate. It
    requires the presence of the :program:`pdftoppm` program as well as
    :program:`convert` from `ImageMagick`_.

    `input_path` may be a string path or a file-like object.

    `output_path` may be a string, a file-like object or :py:obj:`None`.
    If :py:obj:`None`, an :py:class:`io.BytesIO` object is returned
    containing the image. `format` defaults to ``'png'`` if not set
    explicitly in this case.

    Return the name of the output file, or an in-memory file-like object
    (:py:class:`io.BytesIO`) if `output_path` is :py:obj:`None`.

    The idea for behind this conversion mechanism comes from 
    http://stackoverflow.com/a/2002436/2988730. The implementation
    details are described in
    http://stackoverflow.com/a/4846923/2988730.


    .. include:: /link-defs.rst
    """
    if isinstance(input_path, str):
        step1 = [pdftoppm_exe, input_path]
        stdin = None
    else:
        step1 = [pdftoppm_exe]
        stdin = input_path

    if output_path is None:
        # Output to memory
        out = '-'
        if format is None:
            format = 'png'
    elif isinstance(output_path, str):
        # Output to path
        out = output_path
    else:
        # Output to file-like object
        out = '-'

    if format is not None:
        out = ':'.join((format, out))

    step2 = [convert_exe, '-', out]

    proc1 = subprocess.Popen(step1, stdin=stdin, stdout=subprocess.PIPE)
    proc2 = subprocess.Popen(step2, stdin=proc1.stdout, stdout=subprocess.PIPE)
    # Force error in case proc2 dies unexpectedly
    proc1.stdout.close()
    # Ignore output
    sysout, _ = proc2.communicate()

    if isinstance(output_path, str):
        return output_path
    elif output_path is None:
        outputFile = io.BytesIO()
        rewind = True
    else:
        outputFile = output_path
        rewind = False
    outputFile.write(sysout)
    if rewind:
        outputFile.seek(0)
    return outputFile

if __name__ == '__main__':
    from sys import argv, stderr, exit
    from shutil import copyfileobj

    if len(argv) <= 1:
        print('Usage: python -m haggis.files.pdf input.pdf '
              '[output.* | ""] [format]', file=stderr)
        exit(1)

    in_path = argv[1]
    out_path = None
    fmt = None
    if len(argv) > 2:
        if argv[2]:
            out_path = argv[2]
        if len(argv) > 3:
            fmt = argv[3]
    else:
        out_path = None

    x = pdf_to_image(in_path, out_path, fmt)

    if isinstance(x, str):
        print(x)
    else:
        print('In memory object -> tmp.x')
        with open('tmp.x', 'wb') as tmp:
            copyfileobj(x, tmp)
