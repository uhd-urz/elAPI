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
Global configuration and fixture setup for pytest.

This configuration depends on the :mod:`haggis.tests.options` plugin.
"""


from errno import EEXIST
from os import makedirs
from os.path import join
from warnings import warn

from pytest import fixture


@fixture(scope='session')
def plots(request):
    """
    Enables debugging for the fixtures/tests that care about it.

    This fixture will only be set to `True` if the `--plots`
    command-line option is set through the :mod:`skg.tests.options`
    plugin.
    """
    if request.config.getoption('--plots', False):
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot
        except ImportError:
            warn('Unable to import matplotlib: '
                 'plotting will not be enabled.')
            return False

        try:
            from .util import FOLDER
            makedirs(join(request.config.rootdir, FOLDER))
        except OSError as e:
            if e.errno != EEXIST:
                raise
        return True

    return False
