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
Utilities for handling MatPlotLib figures, only available when the
``[plot]`` :ref:`extra <installation-extras>` is installed.

If `matplotlib`_ is not found at import time, this module will have only
a :py:data:`plot_enabled` attribute, which will be :py:obj:`False`. If
`matplotlib`_ is found, on the other hand, :py:data:`plot_enabled` will
be :py:obj:`True`, and all the other documented functions and attributes
of the module will be present.

.. py:data:: plot_enabled

   A boolean value indicating whether the ``[plot]``
   :ref:`extra <installation-extras>` has been installed. If
   :py:obj:`False`, the API will be severely limited.


.. include:: /link-defs.rst 
"""

__all__ = ['plot_enabled']


from contextlib import contextmanager
from io import BytesIO


try:
    from matplotlib import pyplot as plt
    from matplotlib import ticker as mtick
except ImportError:
    from . import _display_missing_extra
    _display_missing_extra('plot', 'matplotlib')
    plot_enabled = False
else:
    import numpy

    __all__.extend([
        'figure_context', 'save_figure', 'set_figure_size', 'set_labels',
        'show_extents', 'semilogx_base', 'semilogy_base', 'loglog_base',
    ])
    plot_enabled = True


if plot_enabled:
    @contextmanager
    def figure_context(*args, **kwargs):
        """
        A context manager that automatically closes the figure that it
        opens.

        Inspired by https://github.com/matplotlib/matplotlib/issues/5218/#issue-110729876
        """
        fig = plt.figure(*args, **kwargs)
        yield fig
        plt.close(fig)


    def save_figure(fig, file=None, size=None, **kwargs):#dpi=300, format='png'
        """
        Save the figure as an image using
        :py:meth:`matplotlib.figure.Figure.savefig`.

        The main value of this method is that it automatically saves to
        memory via a :py:class:`~io.BytesIO` object if a file is not
        specified.

        Parameters
        ----------
        fig:
            The figure to save
        file: str, file-like, or None
            If not :py:obj:`None`, there is no return value. If
            :py:obj:`None`, :py:class:`~io.BytesIO` containing the image
            will be returned. The output will be rewound to the start in
            that case. The default is :py:obj:`None`.
        size: sequence[int]
            The size of the figure in inches, as a 2-element sequence
            ``(w, h)``. If either of the elements is :py:obj:`None`, the
            aspect ratio of the figure will be preserved. Even if only
            the width is specified, `size` must be a sequence.


        All other arguments are passed through directly to
        :py:meth:`~matplotlib.figure.Figure.savefig`. Some common
        options include:

        dpi :
            The resolution of the output image in dots-per-inch.
        format :
            The output format. ``'png'``, ``'svg'``, ``'pdf'`` have good
            support. If not supplied, the default is explicitly set to
            ``'png'``.
        frameon :
            Whether of nor the figure background should be rendered.
            Defaults to :py:obj:`True` if not supplied.
        transparent :
            Whether or not the axes background should be rendered as
            transparent. Defaults to the inverse value of `frameon` if
            not supplied.
        bbox_inches :
            The portion of the figure to save. If ``'tight'``, try to
            use the entire figure. If unset, defaults to ``'tight'``.
        pad_inches :
            The amount of padding to add around the figure when
            `bbox_inches` is ``'tight'``.
        """
        output = BytesIO() if file is None else file
        if size is not None:
            set_figure_size(fig, *size)
        kwargs.setdefault('format', 'png')
        kwargs.setdefault('bbox_inches', 'tight')
        kwargs.setdefault('frameon', fig.frameon)
        kwargs.setdefault('transparent', not kwargs.get('frameon'))
        fig.savefig(output, **kwargs)
        if file is None:
            output.seek(0)
        return output


    def set_figure_size(fig, w=None, h=None):
        """
        Set the size of a figure in inches, optionally preserving the
        aspect ratio.

        If either or the size arguments is :py:obj:`None`, it will be
        scaled to preserve the current aspect ratio. If both are
        :py:obj:`None`, the size is not set at all.
        """
        curr_w, curr_h = fig.get_size_inches()
        if w is None:
            if h is None:
                return
            w = h * curr_w / curr_h
        elif h is None:
            h = w * curr_h / curr_w
        fig.set_size_inches(w, h)


    def set_labels(artists, labels):
        """
        Assign a separate label to each artist in the iterable.

        Useful in labelling each column separately when plotting a
        multi-column array. For example::

            from matplotlib import pyplot as plt
            import numpy as np

            x = np.arange(5)
            y = np.random.ranint(10, size=(5, 3))

            fig, ax = plt.subplots()
            set_labels(ax.plot(x, y), 'ABC')

        Based on https://stackoverflow.com/a/64780035/2988730.

        Parameters
        ----------
        artists :
            Iterable of artists. Any extra entries are silently ignored
            (not labeled).
        labels :
            Iterable of strings. Any extra labels are silently dropped.
        """
        for artist, label in zip(artists, labels):
            artist.set_label(label)


    def show_extents(img, x=None, y=None, ax=None, **kwargs):
        """
        Display an image with the correct x- and y- coordinates,
        adjusted to pixel centers.

        This function is a wrapper around
        :py:meth:`~matplotlib.axes.Axes.imshow`. Normally, ``imshow``
        will scale the axes limits to the outer edges of the image
        when given an ``extent`` argument. However, it is generally
        more accurate to set the centers of the pixels.

        Parameters
        ----------
        img :
            The image to display.
        x : array-like, optional
            The x-coordinates of the pixels. Only the first and last
            coordinate are ever used, so it is safe to pass in any
            sequence of two numbers. ``x[0]`` is the intended
            x-coordinate of the center of the leftmost column of the
            image, while ``x[-1]`` is the x-coordinate of the center of
            the rightmost column.

            Defaults to ``[0, img.shape[1] - 1]``.
        y : array-like, optional
            The y-coordinates of the pixels. Only the first and last
            coordinate are ever used, so it is safe to pass in any
            sequence of two numbers. ``y[0]`` is the intended
            y-coordinate of the center of the topmost row of the image,
            while ``y[-1]`` is the y-coordinate of the center of
            the bottommost column.

            Defaults to ``[0, img.shape[0] - 1]``.
        ax : matplotlib.axes.Axes, optional
            The axes to plot on. If not supplied, a new figure and axes
            are created.
        **kwargs :
            All remaining arguments are passed through to
            :py:meth:`~matplotlib.axes.Axes.imshow`. If an explicit
            ``extent`` is passed in, ``x`` and ``y`` will be ignored.

        Return
        ------
        image : matplotlib.image.AxesImage
            The image object created by
            :py:meth:`~matplotlib.axes.Axes.imshow`.
        """
        if ax is None:
            _, ax = plt.subplots()

        if 'extent' in kwargs:
            extent = kwargs.pop('extent')
        else:
            if x is None:
                x = [0, img.shape[1] - 1]
            else:
                x = numpy.asanyarray(x).ravel()
            if y is None:
                y = [0, img.shape[0] - 1]
            else:
                y = numpy.asanyarray(y).ravel()

            dx = 0.5 * (x[-1] - x[0]) / (img.shape[1] - 1)
            dy = 0.5 * (y[-1] - y[0]) / (img.shape[0] - 1)
            extent = [x[0] - dx, x[-1] + dx,
                      y[-1] + dy, y[0] - dy]

        return ax.imshow(img, extent=extent, **kwargs)


    def _log_base_func(base):
        """
        Convert the base to float and retrieve the simplest function to
        take a logarithm in that base.

        Parameters
        ----------
        base : float
            The base.

        Returns
        -------
        base : float
            The input converted to a :py:class:`float`.
        log : callable
            A function that returns :math:`log_{base}(x)` for any
            array-like `x`.
        """
        base = float(base)
        log = {numpy.e: numpy.log,
               10.0: numpy.log10,
               2.0: numpy.log2}.get(base)

        if log is None:
            lb = numpy.log(base)
            log = lambda x: numpy.log(x) / lb

        return base, log


    def semilogx_base(axes, *args, basex=numpy.e, labelx='e', **kwargs):
        """
        Create a semilogx plot with a custom base.

        The default is to use base `e`.

        This is a convenience wrapper for
        :py:meth:`~matplotlib.axes.Axes.semilogx` which sets ``basex``
        and adds a formatter with a custom label.

        Parameters
        ----------
        axes : matplotlib.axes.Axes
            The axes to plot on.
        *args :
            Normal positional arguments to
            :py:meth:`~matplotlib.axes.Axes.semilogx`.
        basex : float, optional
            Base of the x-axis log-scale. The default is `numpy.e`.
        labelx : str, optional
            The label to use to show the log base for tick marks in the
            x-axis. The default is ``'e'``.
        **kwargs :
            Normal keyword arguments to
            :py:meth:`~matplotlib.axes.Axes.semilogx`.

        Returns
        -------
        list of :py:class:`~matplotlib.lines.Line2D`
            Objects representing the plotted data.
        """
        basex, fnx = _log_base_func(basex)

        if labelx is None:
            labelx = str(basex)

        def xticks(x, pos):
            return f'${labelx}^{{{fnx(x):.0f}}}$'

        lines = axes.semilogx(*args, basex=basex, **kwargs)
        axes.xaxis.set_major_formatter(mtick.FuncFormatter(xticks))
        return lines


    def semilogy_base(axes, *args, basey=numpy.e, labely='e', **kwargs):
        """
        Create a semilogy plot with a custom base.

        The default is to use base `e`.

        This is a convenience wrapper for
        :py:meth:`~matplotlib.axes.Axes.semilogy` which sets ``basey``
        and adds a formatter with a custom label.

        Parameters
        ----------
        axes : matplotlib.axes.Axes
            The axes to plot on.
        *args :
            Normal positional arguments to
            :py:meth:`~matplotlib.axes.Axes.semilogy`.
        basey : float, optional
            Base of the y-axis log-scale. The default is `numpy.e`.
        labely : str, optional
            The label to use to show the log base for tick marks in the
            y-axis. The default is ``'e'``.
        **kwargs :
            Normal keyword arguments to
            :py:meth:`~matplotlib.axes.Axes.semilogy`.

        Returns
        -------
        list of :py:class:`~matplotlib.lines.Line2D`
            Objects representing the plotted data.
        """
        basey, fny = _log_base_func(basey)

        if labely is None:
            labely = str(basey)

        def yticks(y, pos):
            return f'${labely}^{{{fny(y):.0f}}}$'

        lines = axes.semilogy(*args, basey=basey, **kwargs)
        axes.yaxis.set_major_formatter(mtick.FuncFormatter(yticks))
        return lines


    def loglog_base(axes, *args, basex=numpy.e, basey=numpy.e,
                    labelx='e', labely='e', **kwargs):
        """
        Create a log-log plot with a custom base.

        The default is to use base `e`.

        This is a convenience wrapper for
        :py:meth:`~matplotlib.axes.Axes.loglog` which sets ``basex``,
        ``basey``, and adds a formatter with a custom label.

        Parameters
        ----------
        axes : matplotlib.axes.Axes
            The axes to plot on.
        *args :
            Normal positional arguments to
            :py:meth:`~matplotlib.axes.Axes.loglog`.
        basex : float, optional
            Base of the x-axis log-scale. The default is `numpy.e`.
        basey : float, optional
            Base of the y-axis log-scale. The default is `numpy.e`.
        labelx : str, optional
            The label to use to show the log base for tick marks in the
            x-axis. The default is ``'e'``.
        labely : str, optional
            The label to use to show the log base for tick marks in the
            y-axis. The default is ``'e'``.
        **kwargs :
            Normal keyword arguments to
            :py:meth:`~matplotlib.axes.Axes.loglog`.

        Returns
        -------
        list of :py:class:`~matplotlib.lines.Line2D`
            Objects representing the plotted data.
        """
        basex, fnx = _log_base_func(basex)
        basey, fny = _log_base_func(basey)

        if labelx is None:
            labelx = str(basex)
        if labely is None:
            labely = str(basey)

        def xticks(x, pos):
            return f'${labelx}^{{{fnx(x):.0f}}}$'
        def yticks(y, pos):
            return f'${labely}^{{{fny(y):.0f}}}$'

        lines = axes.loglog(*args, basex=basex, basey=basey, **kwargs)
        axes.xaxis.set_major_formatter(mtick.FuncFormatter(xticks))
        axes.yaxis.set_major_formatter(mtick.FuncFormatter(yticks))
        return lines
