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
Tests for the :py:mod:`haggis.math` module.
"""


import numpy
from numpy.testing import assert_allclose, assert_array_equal
from pytest import raises

from ..math import segment_distance, real_divide
from .util import plotting_context, save


class TestSegmentDistance:
    @staticmethod
    def point(t, p1, p2):
        return p1 + t * numpy.subtract(p2, p1)

    def test_one(self, plots):
        p = [0, 3]
        p1 = [-numpy.sqrt(3), 0]
        p2 = [0, 1]
        dist_seg, t_seg = segment_distance(p, p1, p2, return_t=True, segment=True)
        dist_line, t_line = segment_distance(p, p1, p2, return_t=True, segment=False)

        assert_allclose(dist_seg, 2.0, atol=1e-15, rtol=0.0)
        assert_allclose(dist_line, numpy.sqrt(3), atol=1e-15, rtol=0.0)
        assert_allclose(t_seg, 1.5, atol=1e-15, rtol=0.0)
        assert t_seg == t_line

        if plots:
            bounds = numpy.stack((p1, p2), axis=-1)
            p = numpy.array(p)
            pn = self.point(t_line, p1, p2)
            with plotting_context(constrained_layout=True) as fig:
                ax = fig.subplots(1)

                # Draw line
                ax.axline(*bounds.T, color='k', linestyle='--')
                ax.plot(*bounds, color='k', ls='-')

                # Draw normals
                ax.plot(*numpy.stack((p, pn), -1),
                        color='k', linestyle='--')
                ax.plot(*numpy.stack((p, p2), -1), color='k', linestyle='--')

                # Draw markers
                ax.plot(*p, color='k', linestyle='none',
                        marker='o', markersize=10)
                ax.plot(*bounds, color='k', linestyle='none',
                        marker='o', markersize=10)
                ax.plot(*pn, color='k', linestyle='none',
                        marker='o', markerfacecolor='w', markersize=10)

                # Annotate inputs
                ax.text(*p + [-0.15, 0], r'$\vec{p}$',
                        ha='right')
                ax.text(*bounds[:, 0] + [-0.15, 0.1], r'$\vec{p}_1$',
                        ha='right')
                ax.text(*bounds[:, 1] + [-0.15, 0.1], r'$\vec{p}_2$',
                        ha='right')

                # Annotate norms
                ax.text(*0.5 * (p + p2) + [-0.15, 0],
                        fr'$\Delta_1 = {dist_seg:0.0f}$',
                        va='center', ha='center', rotation=90)
                ax.text(*0.5 * (p + pn) + [0.15, 0.1],
                        fr'$\Delta_2 = \sqrt{{{dist_line**2:0.0f}}}$',
                        va='center', ha='center',
                        rotation=numpy.rad2deg(numpy.arctan(-t_line)))

                # Annotate projections
                ax.text(*pn + [0.12, -0.15], f'$t = {t_seg:0.1f}$')

                ax.axis('equal')
                save(fig, __name__, 'one')

    def test_n_points(self, plots):
        p = [[0, 3],
             [-0.5 * (numpy.sqrt(3) + 1), 0.5 * (numpy.sqrt(3) + 1)],
             [1, 1 - numpy.sqrt(3)]]
        p1 = [-numpy.sqrt(3), 0]
        p2 = [0, 1]
        dist_seg, t_seg = segment_distance(p, p1, p2, axis=1, return_t=True,
                                           segment=True)
        dist_line, t_line = segment_distance(p, p1, p2, axis=-1, return_t=True,
                                             segment=False)

        assert_allclose(dist_seg, [2.0, 1.0, 2.0], atol=1e-15, rtol=0.0)
        assert_allclose(dist_line, [numpy.sqrt(3), 1.0, 2.0],
                        atol=1e-15, rtol=0.0)
        assert_allclose(t_seg, [1.5, 0.5, 1.0], atol=1e-15, rtol=0.0)
        assert_array_equal(t_seg, t_line)

        if plots:
            def annotated_line(ax, start, end, label, dist, angle=-60):
                ax.plot([start[0], end[0]], [start[1], end[1]], c='k', ls='--')
                dist = f'{dist:0.0f}' if numpy.isclose(dist, round(dist)) \
                                 else fr'\sqrt{{{dist**2:0.0f}}}'
                ax.text(*0.5 * (start + end) + [0.15, 0.1],
                        fr'$\Delta_{{{label}}} = {dist}$',
                        va='center', ha='center', rotation=angle)

            p = numpy.array(p)
            bounds = numpy.stack((p1, p2), axis=-1)

            with plotting_context(constrained_layout=True) as fig:
                ax = fig.subplots(1)

                # Plot segment
                ax.axline(*bounds.T, color='k', linestyle='--')
                ax.plot(*bounds, color='k', ls='-')

                for i, s, d1, d2, t in zip(
                                 'ABC', p, dist_seg, dist_line, t_line):
                    e1 = self.point(t, p1, p2)

                    # Plot & Label Normals
                    if d1 == d2:
                        annotated_line(ax, s, e1, i, d2)
                    else:
                        e2 = p1 if t < 0 else p2
                        annotated_line(ax, s, e2, f'{i}_2', d2, -90)
                        annotated_line(ax, s, e1, f'{i}_1', d1)

                    # Annotate inputs
                    ax.text(*s + [-0.15, 0], fr'$\vec{{p}}_{{{i}}}$',
                            ha='right')

                    # Annotate projections
                    if not numpy.isclose(t, 0) and not numpy.isclose(t, 1):
                        ax.text(*e1 + [0.12, -0.15], f'$t = {t:0.1f}$')

                # Draw markers
                ax.plot(*p.T, color='k', linestyle='none',
                        marker='o', markersize=10)
                ax.plot(*self.point(t_line[:, None], p1, p2).T,
                        color='k', linestyle='none', marker='o',
                        markerfacecolor='w', markersize=10)
                ax.plot(*bounds, color='k', linestyle='none',
                        marker='o', markersize=10)

                # Annotate Inputs
                ax.text(*bounds[:, 0] + [-0.15, 0.1], r'$\vec{p}_1$',
                        ha='right')
                ax.text(*bounds[:, 1] + [-0.15, 0.1], r'$\vec{p}_2$',
                        ha='right')

                ax.axis('equal')
                save(fig, __name__, 'n_points')

    def test_n_lines(self, plots):
        p = [1.25, 1.25]
        p1 = [[0.5, 2.5], [2, 1.5], [2.5, -0.5], [1, -2],
              [-1.5, -1.5], [-2, -1], [-2, 1], [-1, 2]]
        p2 = [[2.5, 0.5], [2, -1.5], [1, -2], [-1, -2],
              [-2, -1], [-2, 1], [-1, 2], [1.5, 2]]

        dist_seg, t_seg = segment_distance(p, p1, p2, axis=1, return_t=True,
                                           segment=True)
        dist_line, t_line = segment_distance(p, p1, p2, axis=-1, return_t=True,
                                             segment=False)

        sh = numpy.sqrt(1 / 2)
        hsh = sh / 2
        qs170 = numpy.sqrt(170) / 4

        assert_allclose(dist_seg, [hsh, 3 / 4, numpy.sqrt(74) / 4, qs170,
                                   11 * hsh, qs170, 3 * numpy.sqrt(10) / 4,
                                   3 / 4], atol=1e-15, rtol=0.0)
        assert_allclose(dist_line, [hsh, 3 / 4, 3 * sh, 13 / 4,
                                    11 * hsh, 13 / 4, 3 * sh, 3 / 4],
                        atol=1e-15, rtol=0.0)
        assert_allclose(t_seg, [1 / 2, 1 / 12, -1 / 6, -1 / 8,
                                0, 9 / 8, 7 / 4, 9 / 10], atol=1e-15, rtol=0.0)
        assert_array_equal(t_seg, t_line)

        if plots:
            from fractions import Fraction

            def angle(a, b):
                return numpy.rad2deg(numpy.arctan(real_divide(*(b - a)[::-1],
                                                                   numpy.inf)))

            def annotate_projection(fig, ax, t, s, e, r, p):
                x, y = r
                hx = 0.15 + 0.1 * numpy.isclose(y, p[1])
                hy = 0.15 + 0.1 * numpy.isclose(x, p[0])
                x += hx * numpy.sign(x - p[0]) * ~numpy.isclose(x, p[0])
                y += hy * numpy.sign(y - p[1]) * ~numpy.isclose(y, p[1])
                if t:
                    f = Fraction(abs(t)).limit_denominator(10)
                    label = fr'\frac{{{f.numerator}}}{{{f.denominator}}}'
                else:
                    label = 0
                if t < 0:
                    label = '-' + label
                t = ax.text(x, y, f'$t = {label}$', ha='center', va='center',
                            rotation=angle(s, e))
                b = t.get_window_extent(fig.canvas.get_renderer()).\
                                        transformed(ax.transData.inverted())
                ax.update_datalim(b.corners())

            p = numpy.array(p)
            p1 = numpy.array(p1)
            p2 = numpy.array(p2)
            with plotting_context(constrained_layout=True) as fig:
                ax = fig.subplots(1)

                # Draw segments
                for t, s, e in zip(t_seg, p1, p2):
                    ax.axline(s, e, color='k', linestyle='--')
                    ax.plot([s[0], e[0]], [s[1], e[1]],
                            color='k', linestyle='-')

                    # Draw normals
                    r = self.point(t, s, e)
                    ax.plot([p[0], r[0]], [p[1], r[1]],
                            color='k', linestyle='--')

                    # Annontate projections
                    ax.plot(*r, color='k', marker='o',
                            markerfacecolor='w', markersize=10)
                    annotate_projection(fig, ax, t, s, e, r, p)

                # Draw points
                ax.plot(*p, color='k', linestyle='none',
                        marker='o', markerfacecolor='r', markersize=10)
                ax.plot(*p1.T, color='k', linestyle='none',
                        marker='o', markerfacecolor='gray', markersize=10)
                ax.plot(*p2.T, color='k', linestyle='none',
                        marker='o', markerfacecolor='gray', markersize=10)

                # Annotate point
                ax.text(*p + [-0.35, -0.15], fr'$\vec{{p}}$',
                        ha='center', va='center')

                ax.axis('equal')
                save(fig, __name__, 'n_lines')

    def test_broadcast(self):
        p = numpy.array([[0, 1], [1, 0], [0, -1], [-1, 0]])
        p1 = numpy.array([[-0.5, 0.5], [0.5, 0.5], [0.5, -0.5], [-0.5, -0.5]])
        p2 = numpy.array([[0.5, 0.5], [0.5, -0.5], [-0.5, -0.5], [-0.5, 0.5]])

        dist1 = segment_distance(p, p1, p2, axis=1)
        assert_allclose(dist1, [0.5, 0.5, 0.5, 0.5], atol=1e-15, rtol=0.0)

        hs2 = numpy.sqrt(1 / 2)

        dist2 = segment_distance(p[:, None, :], p1, p2, axis=-1)
        assert_allclose(dist2, [[0.5, hs2, 1.5, hs2],
                                [hs2, 0.5, hs2, 1.5],
                                [1.5, hs2, 0.5, hs2],
                                [hs2, 1.5, hs2, 0.5]], atol=1e-15, rtol=0.0)

    def test_error(self):
        p = [[1, 2], [3, 4], [5, 6]]
        p1 = [[1, 2], [3, 4]]
        p2 = [[1, 2], [3, 4]]
        with raises(ValueError, match='broadcast'):
            segment_distance(p, p1, p2)
