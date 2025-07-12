# -*- coding: utf-8 -*-

# haggis: a library of general purpose utilities
#
# Copyright (C) 2024  Joseph R. Fox-Rabinovitz <jfoxrabinovitz at gmail dot com>
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
Utilities for working with PyQt6.

Utilities are only available if PyQt6 is present on the system. Some
attempt is made to support PyQt5 as well, but may be more sporadic.
"""


__all__ = []


try:
    from PyQt6.QtGui import QPixmap, QResizeEvent
    from PyQt6.QtWidgets import QLabel
except ImportError:
    try:
        from PyQt5.QtGui import QPixmap, QResizeEvent
        from PyQt5.QtWidgets import QLabel
    except ImportError:
        from .. import _display_missing_extra
        _display_missing_extra('qt', 'PyQt5 or PyQt6')
        qt_enabled = False
    else:
        qt_enabled = True
else:
    qt_enabled = True


if qt_enabled:
    __all__.extend(['ImageAspectLabel'])


    class ImageAspectLabel(QLabel):
        """
        A label for holding a `QPixmap` image without altering the
        aspect ratio as the label resizes.

        The interface is identical to a normal `QLabel` in all other
        respects.
        """
        def __init__(self):
            super().__init__()
            self.pixmap_width = 1
            self.pixmap_height = 1

        def setPixmap(self, pm: QPixmap):
            if pm is None:
                self.pixmap_width = self.pixmap_height = 0
            else:
                self.pixmap_width = pm.width()
                self.pixmap_height = pm.height()
            self.updateMargins()
            super().setPixmap(pm)

        def resizeEvent(self, a0: QResizeEvent):
            self.updateMargins()
            super().resizeEvent(a0)

        def updateMargins(self):
            if self.pixmap_width <= 0 or self.pixmap_height <= 0:
                self.setContentsMargins(0, 0, 0, 0)
                return
            width, height = self.width(), self.height()
            if width <= 0 or height <= 0:
                return

            if width * self.pixmap_height > height * self.pixmap_width:
                pad = int(width - height * self.pixmap_width / self.pixmap_height + 0.5)
                self.setContentsMargins(pad // 2, 0, pad // 2 + pad % 2, 0)
            else:
                pad = int(height - width * self.pixmap_height / self.pixmap_width + 0.5)
                self.setContentsMargins(0, pad // 2, 0, pad // 2 + pad % 2)
