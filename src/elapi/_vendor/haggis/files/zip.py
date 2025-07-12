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
Utilities for working with zip archives.
"""

__all__ = ['filter', 'remove']


from itertools import repeat
from os import remove as delete
from os.path import splitext
from shutil import copyfileobj
from tempfile import mkstemp
from warnings import warn
from zipfile import ZipFile, ZipInfo


def remove(zipname, *filenames):
    """
    Remove the specified file from the named zip archive.

    Elements of `filenames` may be strings or
    :py:class:`zipfile.ZipInfo` objects. In the latter case, only the
    :py:attr:`~zipfile.ZipInfo.filename` attribute is used to identify
    matches. The other metadata is ignored.

    Raise a warning for any file names that are not found. Actual
    removal is done by recreating the archive minus the filtered
    elements in a temporary file, then overwriting the original with it.
    """
    return filter(zipname, *filenames, filter=None)


def filter(zipname, *filenames, filter=None):
    """
    .. py:function:: filter(zipname, *filenames, filter=None)
       :noindex:
    .. py:function:: filter(zipname, filterDict)
       :noindex:

    Modify the contents of a file or files in the specified zip archive.

    A filter value of :py:obj:`None` removes the selected files.

    There are two calling conventions for this function. In the first
    case, it accepts a sequence of file names or
    :py:class:`zipfile.ZipInfo` objects. `filter` is a function that
    accepts a byte string with the decompressed file contents and
    returns the filtered string to replace the contents with. The
    filtered string may be a true string or bytes.

    In the second case, `filter` is not provided separately, but rather
    as the values in a mapping. The keys are the file names to filter.
    This version is only activated when there is a single additional
    argument besides `zipname`. In this case `filter` is completely
    ignored.

    File contents ares re-inserted with the same metadata as the
    original.
    """
    if len(filenames) != 1 or isinstance(filenames[0], str) or \
                isinstance(filenames[0], ZipInfo):
        iter = zip(filenames, repeat(filter))
    else:
        iter = filenames[0].items()

    filenames = {
        (name if isinstance(name, str) else name.filename): {
            'count': 0, 'filter': filter
        } for name, filter in iter
    }

    # Based heavily on http://stackoverflow.com/a/4653863/2988730 and
    # http://stackoverflow.com/a/25739108/2988730.
    temp_file, temp_name = mkstemp(suffix=splitext(zipname)[1])
    with ZipFile(zipname, 'a') as zin, \
                ZipFile(open(temp_file, 'wb'), 'w') as zout:
        zout.comment = zin.comment
        for item in zin.infolist():
            if item.filename in filenames:
                fileItem = filenames[item.filename]
                fileItem['count'] += 1
                if fileItem['filter'] is None:
                    # Delete file
                    data = None
                else:
                    # Filter file
                    data = fileItem['filter'](zin.read(item))
            else:
                # Passthru file
                data = zin.read(item)

            if data is not None:
                # Write back filtered data. Don't skip empty strings (only None).
                zout.writestr(item, data)

    # Doing it this way will preserve the file permissions
    with open(zipname, 'wb') as fout, open(temp_name, 'rb') as fin:
        copyfileobj(fin, fout)
    delete(temp_name)

    for name, item in filenames.items():
        count = item['count']
        if count > 1:
            warn('"{}" appeared "{}" times '
                 'in "{}"'.format(name, count, zipname))
        elif count == 0:
            warn('"{}" not found in "{}"'.format(name, zipname))

