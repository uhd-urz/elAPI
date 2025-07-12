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
Conversion utilities for PostScript (PS, EPS) files to other formats.

PS and EPS files are very useful formats for creating printable figures
with `matplotlib`_. They support a number of features that are difficult
to achieve with other backends/formats, such as colored TeX strings.

This module relies on the ``[ps]`` :ref:`extra <installation-extras>`,
which implies external programs. As such, this module may be quite
OS-sensitive. Specifically, it requires the main `GhostScript`_ (GS)
program, :program:`gs`.

A small import-guarded block is provided to demo :py:func:`ps_to_image`.


.. include:: /link-defs.rst
"""

__all__ = ['gs_exe', 'ps_to_image']


import subprocess, io, shutil


#: The name of the :program:`gs` executable. Either a full path, or a
#: program that the shell can find on the :envvar:`PATH` is necessary.
gs_exe = 'gs'


#: Mappings of common MatPlotLib-like format names to sensible choices
#: among the GS output devices. Most expected names not in the map are
#: already GS output devices.
_preset_device_map = {
    'png': 'pngalpha',
    'jpg': 'jpeg',
    'bmp': 'bmp16m',
    'pdf': 'pdfwrite'
}


def ps_to_image(input_file, output_file, format='pngalpha', dpi=None):
    """
    Convert a PS or EPS document into an image file.

    EPS files are preferred inputs because they allow for proper
    trimming of the output image margins.

    This function uses the :py:mod:`subprocess` module to operate. It
    requires the presence of the :program:`gs` program from
    `GhostScript`_.

    `input_file` may be a string path or a file-like object.

    `output_file` may be a string, a file-like object or :py:obj:`None`.
    If :py:obj:`None`, an :py:class:`io.BytesIO` object containing the
    image is returned.

    `format` may be either the name of MatPlotLib-like presets or the
    name of a `GhostScript`_ output device. The following is a list of
    preset formats with the GS devices that they map to:

        - ``'png'``: ``pngalpha``
        - ``'jpg'``: ``jpeg``
        - ``'bmp'``: ``bmp16m``
        - ``'pdf'``: ``pdfwrite``

    Preset names do not overlap with any output device, so any value of
    `format` not matching a preset is interpreted as a device name. See
    the docs at http://ghostscript.com/doc/current/Devices.htm for a
    complete list of available output devices.

    `format` defaults to ``'pngalpha'``.

    Returns the name of the output file, or an in-memory file-like object
    (:py:class:`io.BytesIO`) if `output_file` is :py:obj:`None`.


    .. include:: /link-defs.rst
    """
    prog = [
        gs_exe, '-q', '-dSAFER', '-dBATCH', '-dNOPAUSE',
        '-dUseTrimBox', '-dEPSCrop'
    ]

    if format in _preset_device_map:
        device = _preset_device_map[format]
    else:
        device = format
    prog.append('-sDEVICE=' + device)

    if dpi:
        prog.append('-r{}'.format(dpi))

    rewind = False
    if isinstance(output_file, str):
        # Output to file
        prog.append('-sOutputFile=' + output_file)
        stdout = None
    else:
        prog.append('-sOutputFile=-')
        if output_file is None:
            # Output to memory
            output_file = io.BytesIO()
            rewind = True
        stdout = output_file

    if isinstance(input_file, str):
        prog.append(input_file)
        stdin = None
        input_file = None
    else:
        prog.append('-_')
        stdin = subprocess.PIPE

    proc = subprocess.Popen(prog, stdin=stdin, stdout=stdout)
    if proc.stdin:
        shutil.copyfileobj(input_file, proc.stdin)
        proc.stdin.close()
    proc.wait()

    if rewind:
        output_file.seek(0)

    return output_file


if __name__ == '__main__':
    from sys import argv

    if len(argv) <= 1:
        raise ValueError('Usage: python -m haggis.files.ps '
                         'input.[e]ps [output.* | ""] [format]')
    input_file = argv[1]
    output_file = None
    kwargs = {}
    if len(argv) > 2:
        if argv[2]:
            output_file = argv[2]
        if len(argv) > 3:
            kwargs['format'] = argv[3]
    else:
        output_file = None

    x = ps_to_image(input_file, output_file, **kwargs)

    if isinstance(x, str):
        print(x)
    else:
        print('In memory object -> tmp.x')
        with open('tmp.x', 'wb') as tmp:
            shutil.copyfileobj(x, tmp)
