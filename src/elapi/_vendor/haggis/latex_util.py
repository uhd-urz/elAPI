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
Utilities for processing bits of latex using matplotlib for rendering.

The `matplotlib`_ setup routines are based on
http://stackoverflow.com/a/38008501/2988730.

This module relies on the ``[plot]`` and ``[latex]``
:ref:`extras <installation-extras>`. The :py:func:`render_latex` function
does not rely on ``[plot]``. All the other functions work with
`matplotlib`_. See :py:data:`haggis.mpl_util.plot_enabled`.


.. include:: /link-defs.rst
"""

__all__ = [
    'add_use_package', 'render_latex', 'package_list',
    'latex_exe', 'dvips_exe', 'convert_exe',
]


import tempfile, subprocess, io
from os import path


#: The list of packages loaded into the LaTeX preamble when this module
#: is imported. This list gets updated with every call to
#: :py:func:`add_use_package`. This allows :py:func:`setup_mpl` to work
#: correcly even when backends are changed under the ``[plot]`` extra.
package_list = ['amsmath', 'color', 'dashrule']  # Candidates: amssym, tikz


#: The name of the :program:`latex` executable. Either a full path, or a
#: program that the shell can find on the :envvar:`PATH` is necessary.
latex_exe = 'latex'


#: The name of the :program:`dvips` executable. Either a full path, or a
#: program that the shell can find on the :envvar:`PATH` is necessary.
dvips_exe = 'dvips'


#: The name of the `ImageMagick`_ :program:`convert` executable. Either
#: a full path, or a program that the shell can find on the
#: :envvar:`PATH` is necessary.
convert_exe = 'convert'


def add_use_package(package_name):
    r"""
    Add a single package via ``\usepackage{package_name}`` to the
    LaTeX premble.
    """
    if package_name not in package_list:
        package_list.append(package_name)


def render_latex(formula, file=None, format='png', *, fontsize=12, dpi=None,
                 transparent=False, bgcolor='white', fgcolor='black'):
    """
    Render a simple LaTeX formula into an image using external programs.

    If `file` is :py:obj:`None` (the default), return a
    :py:class:`~io.BytesIO` object containing the rendered image in PNG
    format. The stream is rewound, so can be read immediately.
    Otherwise, output to the specified file (which may be a file name
    string or any file-like object).

    The sequence of system commands run by this function is based
    largely on :program:`text2im` (http://www.nought.de/tex2im.php).
    """
    preamble = '\n'.join(r'\usepackage{%s}' % pkg for pkg in package_list)
    content = '\n'.join([
        r'\documentclass[{fontsize}pt]{{article}}',
        r'{preamble}',
        r'\usepackage[dvips]{{graphicx}}',
        r'\pagestyle{{empty}}',
        r'\pagecolor{{{bgcolor}}}',
        #r'\DeclareMathSizes{{{fontsize}}}{{{fontsize}}}{{{fontsize2}}}{{{fontsize3}}}',
        r'\begin{{document}}',
        r'{{\color{{{fgcolor}}}',
        r'$$ {formula} $$',
        r'}}\end{{document}}'
    ])
    content = content.format(
        preamble=preamble, formula=formula, bgcolor=bgcolor, fgcolor=fgcolor,
        fontsize=fontsize#, fontsize2=fontsize-2, fontsize3=fontsize-4
    )
    latex = [
        latex_exe, '-output-format=dvi', '-halt-on-error', #'-interaction=batchmode' 
    ]
    dvips = [dvips_exe, '-o', '-']
    convert = [
        convert_exe, '+adjoin', '-antialias'
    ]

    if dpi:
        convert.extend(['-density', '{0}x{0}'.format(dpi)])
    if transparent:
        convert.extend(['-transparent', bgcolor])

    rewind = False
    convert.append('-')                           # Input from pipe
    if isinstance(file, str):
        convert.append('{}:{}'.format(format, file))  # Output to file
        stdout = None
    else:
        if file is None:
            file = io.BytesIO()
            rewind = True
        convert.append(format + ':-')             # Output to pipe
        stdout = file

    with tempfile.TemporaryDirectory() as tmpdir:
        latex.append('-output-directory=' + tmpdir)
        proc1 = subprocess.Popen(latex, stdin=subprocess.PIPE,
                                 stdout=subprocess.DEVNULL,
                                 universal_newlines=True)
        proc1.communicate(input=content)

        dvips.extend(['-E', path.join(tmpdir, 'texput.dvi')])
        proc2 = subprocess.Popen(dvips, stdin=None, stdout=subprocess.PIPE,
                                 stderr=subprocess.DEVNULL)
        proc3 = subprocess.Popen(convert, stdin=proc2.stdout, stdout=stdout)
        proc2.stdout.close()
        proc3.communicate()

    if rewind:
        file.seek(0)
    return file


# Do this first to verify the [plot] extra
from . import mpl_util
if mpl_util.plot_enabled:
    import matplotlib


    __all__.extend([
        'setup_mpl', 'render_latex_mpl', 'pgf_tex_system',
    ])


    #: The name of the LaTeX PGF system, obtained from::
    #:
    #:    latex -v
    pgf_tex_system = 'pdftex'


    def setup_mpl():
        """
        Sets up the packages that should be used by `matplotlib`\ 's
        LaTeX processor.

        In addition to ensuring that some basic packages are imported in
        the preamble, this method enables latex usage in `matplotlib`_
        text elements such as titles and axis labels.

        This method must be called manually by any package wishing to
        use :py:func:`render_latex_mpl` with full capabilities. It
        should be used when the backend is changed to and from ``'pgf'``
        as well.


        .. include:: /link-defs.rst
        """
        # See http://matplotlib.org/users/usetex.html for details on text keys,
        # and http://matplotlib.org/users/pgf.html for details on PGF backend
        if matplotlib.get_backend() == 'pgf':
            from matplotlib.backends.backend_pgf import FigureCanvasPgf
            matplotlib.backend_bases.register_backend('pdf', FigureCanvasPgf)
            matplotlib.backend_bases.register_backend('png', FigureCanvasPgf)
            matplotlib.rc('pgf', texsystem=pgf_tex_system)
        else:
            matplotlib.rc('text', usetex=True)

        for package in package_list:
            add_use_package(package)


    def add_use_package(package_name):
        r"""
        Add a single package via ``\usepackage{package_name}`` to the
        list of `matplotlib`_\ 's LaTeX imports.

        Imports can be added to ``text.latex.preamble`` or
        ``pgf.preamble`` RC keys, depending on the current backend.
        Packages are also automatically added to the preamble of non-MPL
        rendered LaTeX.


        .. include:: /link-defs.rst
        """
        if package_name not in package_list:
            package_list.append(package_name)

        def set_preamble(which):
            preamble = matplotlib.rcParams.setdefault(which, [])
            use_str = r'\usepackage{%s}' % package_name
            if use_str not in preamble:
                preamble.append(use_str)

        if matplotlib.get_backend() == 'pgf':
            set_preamble('pgf.preamble')
        else:
            set_preamble('text.latex.preamble')


    def render_latex_mpl(formula, file=None, fontsize=12, **kwargs):
        """
        Render a simple LaTeX formula into an image using
        `matplotlib`_ figures.

        If `file` is :py:obj:`None` (the default), returns a
        :py:class:`~io.BytesIO` object containing the rendered image in
        the specified format. The stream is rewound, so can be read
        immediately. Otherwise outputs to the specified file (which may
        be a file name string or any file-like object).

        All arguments besides `file` and `fontsize` are passed through to
        :py:meth:`matplotlib.figure.Figure.savefig`.

        This method is based on the following Stack Overflow answer:
        http://stackoverflow.com/a/31371907/2988730


        .. include:: /link-defs.rst
        """
        with mpl_util.figure_context(figsize=(0.01, 0.01)) as fig:
            fig.text(0, 0, u'${}$'.format(formula), fontsize=fontsize,
                     horizontalalignment='left', verticalalignment='bottom')
            fig.frameon = False
            return mpl_util.save_figure(fig, file, bbox_inches='tight')


if __name__ == '__main__':
    if mpl_util.plot_enabled:
        setup_mpl()
    eqn = (r'P_k = \frac{\sqrt{\frac{1}{N - 1}\sum_{i=1}^{N} '
                                    r'(x_i - \bar{x})^2}}{\bar{x}}')
    render_latex(eqn, file='renderer_demo.png')
    if mpl_util.plot_enabled:
        render_latex_mpl(eqn, format='png', file='renderer_demo_mpl.png')

    mat = (r'\begin{bmatrix} '
           r'a_{11} & b_{12} & \dots  & z_{1n} \\ '
           r'a_{21} & b_{22} & \dots  & z_{2n} \\ '
           r'\vdots & \vdots & \ddots & \vdots \\ '
           r'a_{n1} & a_{n2} & \dots  & z_{nn} '
           r'\end{bmatrix}')
    render_latex(mat, file='renderer_demo2.png')
    if mpl_util.plot_enabled:
        render_latex_mpl(mat, format='png', file='renderer_demo2_mpl.png')

    text = (r'\textcolor{blue}{ -\bullet- \; }')
    render_latex(text, file='renderer_demo3.png')
    if mpl_util.plot_enabled:
        render_latex_mpl(text, format='png', file='renderer_demo3_mpl.png')

