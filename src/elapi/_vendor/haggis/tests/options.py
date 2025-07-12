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
Pytest plugin for processing the haggis-specific command-line options.
"""


def pytest_addoption(parser):
    """
    Add options to the default command line.

    The following options are added:

    `--plots`
        Draw plots of x-values, y-values and fit comparisons. This
        option checks if matplotlib is installed, and issues a warning
        if not.

    """
    parser.addoption("--plots", action="store_true", default=False,
                     help="Generate graphical plots of input data")
