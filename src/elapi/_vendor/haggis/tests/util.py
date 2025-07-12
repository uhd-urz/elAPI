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
# Version: 12 Jan 2022: Initial Coding

"""
Collection of testing utilities for common actions.
"""


from contextlib import contextmanager
from os.path import join


FOLDER = '.haggis_test'


@contextmanager
def plotting_context(*args, **kwargs):
    """
    Context manager that imports matplotlib as necessary, creates a
    figure, and closes it on exit.

    All parameters are passed directly to
    :py:func:`~matplotlib.pyplot.figure`.
    """
    from matplotlib import pyplot as plt
    figure = plt.figure(*args, **kwargs)
    yield figure
    plt.close(figure)


def save(fig, module, label, debug=False, dpi=300):
    """
    Saves a figure in the standard test output directory.

    The figure name is nomalized with the name of the calling module.
    """
    ext = 'debug.png' if debug else 'png'
    label = f'{module}-{label}.{ext}'

    fig.savefig(join(FOLDER, label), dpi=dpi)
