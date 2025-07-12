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
Math utility functions that are otherwise uncategorized.
"""

__all__ = [
    'ang_diff_abs', 'ang_diff_min', 'ang_diff_pos', 'count_divisors',
    'ellipse', 'first_primes', 'full_width_half_max', 'primes_up_to',
    'real_divide', 'rms', 'round_sig', 'segment_distance', 'threshold'
]


import itertools
import math
import numpy
from scipy.stats import iqr

from .mapping import option_lookup


def round_sig(x, n):
    """
    Round the number `x` to `n` significant figures.

    Based on https://stackoverflow.com/a/3411435/2988730
    """
    if not x:
        return x
    digits = -math.floor(math.log10(abs(x))) + (n - 1)
    return round(x, digits)


def ellipse(*args, num_points=1e3, **kwargs):
    r"""
    .. py:function:: ellipse(a, [b=0,] c, d, e, f, *, numPoints=1e3)
       :noindex:
    .. py:function:: ellipse(a, b, h, k, *, theta=0, numPoints=1e3)
       :noindex:

    Return x-y arrays for an ellipse in one of two standard forms.

    The equations are either the quadratic form,

    .. math::

       ax^2 + bxy + cy^2 + dx + ey + f = 0

    or the simplified form,

    .. math::

       \frac{(x - h)^2}{a^2} + \frac{(y - k)^2}{b^2} = 1

    The first form allows for rotated ellipses through the :math:`bxy`
    coupling term. The second form allows it through the explicit
    (optional) angle parameter `theta`, specified in radians
    counterclockwise about ``(h, k)``.

    The number of points is specified by `numPoints`. Points are evenly
    distributed by angle, not by arc-length (unless the ellipse is a
    circle). The default number of points is 1000.

    Return
    ======
    x : numpy.ndarray
        Array of `num_points` x-coordinates.
    y : numpy.ndarray
        Array of `num_points` y-coordinates.

    Notes
    =====
    This code is loosely based on my Stack Overflow answer:
    http://stackoverflow.com/a/41231100/2988730, which is in turn
    loosely based on the forum post at
    http://www.sosmath.com/CBB/viewtopic.php?t=17029
    """
    t = numpy.linspace(0, 2 * math.pi, num_points)

    coeffCount = len(args)
    if 5 <= coeffCount <= 6:
        if coeffCount == 5:
            a, c, d, e, f = args
            b = 0
        if len(args) == 6:
            a, b, c, d, e, f = args
        if kwargs:
            raise ValueError('Only num_points can be a keyword '
                             'for quadratic form of ellipse')

        discriminant = b**2 - 4 * a * c
        if discriminant >= 0.0:
            name = 'parabloa' if discriminant == 0.0 else 'hyperbola'
            raise ValueError('Discriminant shows this to be '
                             'a {}, not an ellipse'.format(name))
        if b == 0:
            theta = 0
        else:
            theta = 0.5 * math.atan(b / (a - c))
            sin = math.sin(theta)
            cos = math.cos(theta)
            aa = a * cos**2 + b * sin * cos + c * sin**2
            cc = a * sin**2 - b * sin * cos + c * cos**2
            dd = d * cos + e * sin
            ee = -d * sin + e * cos
            a, b, c, d, e = aa, 0, cc, dd, ee
        ax_x = 1.0 / math.sqrt(a)
        ax_y = 1.0 / math.sqrt(c)
        scale = math.sqrt(d**2 / (4 * a) + e**2 / (4 * c) - f)
        h = -d / (2 * a)
        k = -e / (2 * c)
        x = xx = h + ax_x * scale * numpy.sin(t)
        y = yy = k + ax_y * scale * numpy.cos(t)
        if theta:
            x = xx * cos - yy * sin
            y = xx * sin + yy * cos
    elif coeffCount == 4:
        ax_x, ax_y, h, k = args
        x = xx = ax_x * numpy.sin(t)
        y = yy = ax_y * numpy.cos(t)
        theta = float(kwargs.pop('theta', 0.0))
        if theta:
            sin = math.sin(theta)
            cos = math.cos(theta)
            x = h + xx * cos - yy * sin
            y = k + xx * sin + yy * cos
        if kwargs:
           raise ValueError('Only num_points and theta can be a keyword '
                            'argument for simple form of ellipse')
    else:
        raise ValueError('Argument list must have 4 to 6 positional elements')

    return x, y


def full_width_half_max(x, y, factor=0.5, baseline=0.0, interp='linear', *,
                        return_points=False):
    """
    Compute the full-width, half-max metric for a dataset.

    The full-width half-max is the distance between where the data rises
    to half of the maximum for the last time before the max itself and
    where it falls below half of the maximum for the first time above
    the maximum.

    The actual fraction of the maximum that is used can be adjusted with
    `factor` (which defaults to 0.5). `factor` can be a number or the
    string ``'sigma'``, in which case it will be set to
    :math:`e^{-\\frac{1}{4}}`, the height of a Gaussian with unit
    amplitude one standard devition away from the mean. A fixed non-zero
    baseline can also be provided so that it does not have to be
    subtracted from `y` before being passed in.

    Since the actual `y` array is unlikely to contain the exact half-max
    value, an interpolation can be done. Currently, the following
    interpolation methods are supported:

      - ``'linear'``: linear interpolation betweent the x- and y-values
        surrouding the actual half-max point.
      - ``'nearest'``: nearest neighbor, i.e., use the x-value of the
        y-value that is closest to the half-max.

    Normally, a single scalar is returned. If `return_points` is
    :py:obj:`True`, however, two two-element tuples are returned as the
    second and third argument. Each tuple will contain an x-y pair of
    the intersection coordinates used to approximate the main return
    value. The first tuple will be for the left (rising) edge and the
    second will be for the right (trailing) edge.
    """
    imax = numpy.argmax(y)
    if factor == 'sigma':
        factor = math.exp(-0.25)
    # Also can be written as factor * y[imax] + (1.0 - factor) * baseline
    halfmax = factor * (y[imax] - baseline) + baseline
    # Always use <= to allow first and last y-value if they match exactly.
    rising = (y[:imax] <= halfmax) & (y[1:imax + 1] > halfmax)
    falling = (y[imax:-1] > halfmax) & (y[imax + 1:] <= halfmax)
    if not numpy.any(rising):
        raise ValueError(
            'left edge does not fall below {} of max'.format(factor)
        )
    if not numpy.any(falling):
        raise ValueError(
            'right edge does not fall below {} of max'.format(factor)
        )
    # Select last rising, first falling index.
    # Initial [0] because of nonzero's weird tuple return
    rising_index = numpy.nonzero(rising)[0][-1] + numpy.arange(2)
    falling_index = numpy.nonzero(falling)[0][0] + imax + numpy.arange(2)
    if interp == 'linear':
        def linterp(x0, x1, y0, y1, y):
            return x0 + (x1 - x0) * (y - y0) / (y1 - y0)
        rising = (linterp(*x[rising_index], *y[rising_index],halfmax),
                  halfmax)
        falling = (linterp(*x[falling_index], *y[falling_index], halfmax),
                   halfmax)
    elif interp == 'nearest':
        def nearest(ys, inds, y):
            return inds[numpy.argmin(numpy.abs(ys[inds] - y))]
        rising_i = nearest(y, rising_index, halfmax)
        falling_i = nearest(y, falling_index, halfmax)
        rising = (x[rising_i], y[rising_i])
        falling = (x[falling_i], y[falling_i])
    else:
        raise ValueError(
            'Invalid value of `interp` parameter. Expected '
            '{{"linear", "nearest"}}, found "{}".'.format(interp)
        )

    if return_points:
        return falling[0] - rising[0], rising, falling

    return falling[0] - rising[0]


def primes_up_to(n):
    """
    Generate a set containing all the primes less than or equal to `n`.

    `n` must be a number that represents an array size that can exist
    in memory. The implementation uses an extremely unoptimized version
    of the sieve of Eratosthenes.

    Parameters
    ----------
    n : int
        The largest number to generate primes up to (exclusive). If you
        want an inclusive range, add 1 to this input.

    Return
    ------
    primes : set
        A set of all the primes less than `n`.
    """
    sieve = numpy.arange(2, n, dtype=numpy.int_)
    for i in range(n - 2):
        p = sieve[i]
        if p:
            sieve[i+p::p] = 0
    return sieve[numpy.nonzero(sieve)]


def first_primes(n):
    """
    Generate a set with the first `n` prime numbers.

    This is a toy method that should probably not be used for large
    prime numbers. Instead of actively discarding all multiples of
    found primes, it checks new candidates against each element of the
    current set of primes.

    Parameters
    ----------
    n : int

    Return
    ------
    primes : set
    """
    primes = set()
    for i in itertools.count(2):
        if all(i % p for p in primes):
            primes.add(i)
        if len(primes) == n:
            break
    return primes


def count_divisors(n):
    """
    Counts the divisors of natural number `n`, including 1 and itself.

    For example, ``28`` has divisors ``1, 2, 4, 7, 14, 28``, so
    ``count_divisors(28) == 7``.
    """
    count = 0
    limit = int(math.sqrt(n))
    # Add one if the number is a square (limit won't be part of loop)
    extra = (limit**2 == n)
    for i in range(2, limit):
        if not n % i:
            count += 1
    # Add one to count because loop does not check if 1/n are factors
    return (count + 1) * 2 + extra


def real_divide(a, b, zero=0, out=None):
    """
    Divide real numbers, where the second may be zero.

    Parameters
    ----------
    a : array-like
        The divisor.
    b : array-like
        The dividend
    zero :
        The value to place in locations where `b` is zero.
    out : array-like or None
        An array of a suitable type and size to hold the result.
        If `None`, a new output array is allocated.

    Return
    ------
    numpy.ndarray :
        The result of applying :py:func:`numpy.true_divide` to `a` and
        `b`, except that elements corresponding to zeros in `b` are set
        to `zero` instead of actually being computed.
    """
    mask = (b != 0)
    result = numpy.true_divide(a, b, where=mask, out=out)
    if result.ndim > 0:
        result[~mask] = zero
    elif ~mask:
        result = zero
    return result


_thresholding_directions = {
    'le': numpy.less_equal,    '<=': numpy.less_equal,
    'lt': numpy.less,          '<': numpy.less,
    'ge': numpy.greater_equal, '>=': numpy.greater_equal,
    'gt': numpy.greater,       '>': numpy.greater,
}

_thresholding_types = {
    'std': lambda x, n: numpy.mean(x) + n * numpy.std(x),
    'iqr': lambda x, n: numpy.median(x) + n * iqr(x),
    'rms': lambda x, n: n * numpy.sqrt(numpy.square(x).mean()),
    'raw': lambda x, n: n,
}

def threshold(arr, thresh=3, type='std', direction='le'):
    """
    Apply a threshold to an array (usually an image).

    Parameters
    ----------
    arr : array-like
        The array to threshold.
    direction : str
        Which direction is considered passing:

        - ``'le'`` or ``'<='``: Elements of `arr` <= the threshold are
          marked `True`.
        - ``'lt'`` or ``'<'``: Elements of `arr` < the threshold are
          marked `True`.
        - ``'ge'`` or ``'>='``: Elements of `arr` >= the threshold are
          marked `True`.
        - ``'gt'`` or ``'>'``: Elements of `arr` > the threshold are
          marked `True`.

        The default is ``'le'``.
    thresh : array-like, optional
        The threshold value to apply. Must broadcast to the shape of the
        array. The exact meaning of the value is determined by `type`.
        The default is ``3`` (for 3-sigma thresholding).
    type : str, optional
        The type of threshold to use:

        - ``'std'``: Mean plus `threshold` times standard deviation.
        - ``'iqr'``: Median plus `threshold` times interqartile range.
        - ``'rms'``: `threshold` times the root-mean square.
        - ``None``, ``''``, ``'raw'``: Use `threshold` as-is.

        The default is 'std'.

    Returns
    -------
    numpy.ndarray :
        A boolean array of the same size and shape as `arr`, containing
        a mask indicating which elements pass threshold.
    """
    dmethod = option_lookup('direction', _thresholding_directions,
                            direction, key_func=str.lower)
    
    tmethod = option_lookup('type', _thresholding_types,
                            type or 'raw', key_func=str.lower)

    arr = numpy.asanyarray(arr)

    return dmethod(arr, tmethod(arr, thresh))


def ang_diff_pos(theta1, theta2, full=2.0 * numpy.pi):
    r"""
    Find the positive angular difference from `theta1` to `theta2`,
    normalized to :math:`[0, 2 \pi)`.

    The positive difference is the angle going in the positive
    direction from `theta1` to `theta2`, normalized to be in the range
    :math:`[0, 2 \pi)`.

    The return value can be computed without branching as ::

        ang_diff_pos = fmod(fmod(theta2 - theta1, full) + full, full)

    Inputs can be scalars or arrays. Arrays must broadcast together.

    Parameters
    ----------
    theta1 : array-like
        The start angle or angles, in radians.
    theta2 : array-like
        The end angle or angles, in radians.
    full : float
        The period of a full circle. Defaults to :math:`2 \pi`. Use 360
        for data in degrees, 400 for gradians, 6400 for mils, etc.

    Returns
    -------
    numpy.ndarray :
        An array containing the broadcasted positive normalized
        difference of the two inputs.
    """
    return numpy.fmod(numpy.fmod(theta2 - theta1, full) + full, full)


def ang_diff_min(theta1, theta2, full=2.0 * numpy.pi):
    r"""
    Find the angular difference from `theta1` to `theta2`, with the
    minimum absolute value normalized to :math:`[-\pi, \pi)`.

    The positive difference is the angle going in the positive
    direction from `theta1` to `theta2`, normalized to be in the range
    :math:`[0, 2 \pi)`. The negative difference is the angle going in
    the negative direction. This function returns the smaller of the
    two by absolute value.

    The return value can be computed without branching by rotating by
    half a circle before applying the moduli, then rotating back::

        ang_diff_min = fmod(fmod(theta2 - theta1 + 0.5 * full, full) +
                            full, full) - 0.5 * full

    Inputs can be scalars or arrays. Arrays must broadcast together.

    Parameters
    ----------
    theta1 : array-like
        The start angle or angles, in radians.
    theta2 : array-like
        The end angle or angles, in radians.
    full : float
        The period of a full circle. Defaults to :math:`2 \pi`. Use 360
        for data in degrees, 400 for gradians, 6400 for mils, etc.

    Returns
    -------
    numpy.ndarray :
        An array containing the broadcasted sign-preserving normalized
        difference of the two inputs with the smallest absolute value.
    """
    half = 0.5 * full
    # Broken out for readability
    step1 = numpy.fmod(theta2 - theta1 + half, full)
    return numpy.fmod(step1 + full, full) - half


def ang_diff_abs(theta1, theta2, full=2.0 * numpy.pi):
    r"""
    Find the absolute value of the minimum angular difference from
    `theta1` to `theta2`, normalized to :math:`[0, \pi)`.

    The minimum absolute difference is the smallest angle to get from
    `theta1` to `theta2` going in either direction, normalized to be in
    the range :math:`[0, \pi)`.

    The return value can be computed without branching as ::

        ang_diff_abs = abs(ang_diff_min(theta1, theta2, full))

    Inputs can be scalars or arrays. Arrays must broadcast together.

    Parameters
    ----------
    theta1 : array-like
        The start angle or angles, in radians.
    theta2 : array-like
        The end angle or angles, in radians.
    full : float
        The period of a full circle. Defaults to :math:`2 \pi`. Use 360
        for data in degrees, 400 for gradians, 6400 for mils, etc.

    Returns
    -------
    numpy.ndarray :
        An array containing the broadcasted minimum absolute normalized
        difference of the two inputs.
    """
    return numpy.abs(ang_diff_min(theta1, theta2, full))


def rms(arr, axis=None, bias=0, weights=None, ddof=0, out=None):
    """
    Comute the root-mean-square (RMS) of an array about an arbitrary
    bias.

    Parameters
    ----------
    arr : array-like
        The input array.
    axis : int or tuple or None, optional
        The axis or axes to compute the RMS along. The average of the
        squares will be taken along this axis or axes. None (the
        default) indicates the entire raveled array.
    bias : array-like, optional
        The offset about which to compute the RMS. The default is zero
        for standard RMS. The bias must broadcast to `arr`. Setting
        ``bias=numpy.mean(arr, axis=axis, keepdims=True)`` is equivalent
        to computing ``numpy.std(arr, axis=axis)``.
    weights : array-like, optional
        The weights to apply in the mean portion. Similar behavior to
        :py:func:`numpy.average`. Assumed to be all ones if omitted. If
        `axis` is None, must broadcast to `arr`. Otherwise, must be
        the same shape as either `arr[axis]` or `arr`.
    ddof : scalar, optional
        The degrees of freedom to subtract from the denominator. Defaults
        to zero.
    out : numpy.ndarray or None, optional
        The array to output results into, if not None. Use carefully,
        as *all* intermediate calculations will be placed into this
        array: a square, a mean and a square root. Using an output of
        an inappropriate type may lead to errors. The default is None.

    Return
    ------
    rms : numpy.ndarray
        The RMS of `arr` about `bias` along `axis`.
    """
    sq = numpy.square(numpy.asanyarray(arr) - bias, out=out)
    weights = numpy.array([1]) if weights is None \
                                            else numpy.asanyarray(weights)
    if axis is None:
        sq = sq.ravel()
        weights = weights.ravel()
    else:
        axis = numpy.core.multiarray.normalize_axis_index(axis, sq.ndim)
        if weights.ndim < sq.ndim:
            weights = numpy.reshape(weights,
                                    weights.shape + (1,) * (sq.ndim - axis - 1))
    weights = numpy.broadcast_to(weights, sq.shape)
    return numpy.sqrt(numpy.sum(sq * weights, axis=axis, out=out) / (weights.sum(axis=axis) - ddof), out=out)


def segment_distance(p, p1, p2, axis=None, return_t=False, segment=True):
    r"""
    Find the distance between an N-dimensional point and a line or line
    segment.

    The distance from a point to a line in N dimensions is the length
    of a normal dropped to the line. Using the fact that the dot
    product of orthogonal vectors is we can find the point
    :math:`\vec{p}_0` on the line that corresponds to this location.

    First, parametrize the points on the line through parameter
    :math:`t` as

    .. math::

       \vec{\ell} = \vec{p}_1 + t (\vec{p}_2 - \vec{p}_1)

    Then set up the equation with dot-products and solve for :math:`t`:

    .. math::

       (\vec{p} - \vec{p}_0) \cdot (\vec{p}_2 - \vec{p}_1) = 0

    .. math::

       (\vec{p} - \vec{p}_1 - t (\vec{p}_2 - \vec{p}_1)) \cdot (\vec{p}_2 - \vec{p}_1) = 0

    .. math::

       t (\vec{p}_2 - \vec{p}_1) \cdot (\vec{p}_2 - \vec{p}_1) = (\vec{p} - \vec{p}_1) \cdot (\vec{p}_2 - \vec{p}_1)

    .. math::

       t = \frac{(\vec{p} - \vec{p}_1) \cdot (\vec{p}_2 - \vec{p}_1)}{\left\lVert\vec{p}_2 - \vec{p}_1\right\rVert ^ 2}

    .. math::

       \vec{p}_0 = \vec{p}_1 + \frac{(\vec{p} - \vec{p}_1) \cdot (\vec{p}_2 - \vec{p}_1)}{\left\lVert\vec{p}_2 - \vec{p}_1\right\rVert ^ 2} (\vec{p}_2 - \vec{p}_1)

    The value of :math:`t` represents the location of :math:`\vec{p}_0`
    in relationship to :math:`\vec{p}_1` and :math:`\vec{p}_2`: values
    in the range :math:`[0, 1]` are on the line segment, negative
    values are on the side closer to :math:`\vec{p}_1`, and values
    greater than one are on the side of the line closer to
    :math:`\vec{p}_2`.

    The value of :math:`t` at the closest approach can be returned by
    setting ``return_t=True``. The value returned in this case applies
    to the entire line, even if ``segment == True`` and the closest
    point is one of the endpoints of the line segment.

    Parameters
    ----------
    p : array-like
        The target point. Must broadscast to `p1` and `p2`.
    p1 : array-like
        The start of the line segment. Must broadcast to the same shape
        as `p` and `p2`.
    p2 : array-like
        The end of the line segment. Must broadcast to the same shape
        as `p` and `p1`.
    axis : int or None
        The axis corresponding to the point vectors in the broadcasted
        arrays. If `None`, all point arrays are raveled.
    return_t: bool
        If `True`, return an additional value indicating the parameter
        :math:`t` at the distance of closest approach along the line.
        This will be the same regargless of `segment`.
    segment: bool
        If `True`, find the nearest point on the line segment bounded
        by `p1` and `p2` rather than the line passing between them.

    Returns
    -------
    dist : float or ~numpy.ndarray
        Distance from `p` to the line or line segment passing through
        `p1` and `p2`. The shape of the result is the broadcasted shape
        of the inputs, collapsed along `axis`.

        Scalar if `axis is None` or the inputs are all one-dimensional.
    t : float or ~numpy.ndarray
        An array of the same shape as `dist` containing the value of
        parameter :math:`t` for each line. The parameter is the
        location of the normal from `p` to the line passing through
        `p1` and `p2`, regardless if the distance is to the line
        segment or the line.

        Returned only if `return_t` is set.
    """
    p, p1, p2 = numpy.broadcast_arrays(p, p1, p2)
    seg = p2 - p1
    norm2_seg = (seg * seg).sum(axis=axis, keepdims=True)
    t = ((p - p1) * seg).sum(axis=axis, keepdims=True) / norm2_seg
    p0 = p1 + t * seg

    if segment:
        dist = numpy.empty_like(p0)
        mask1 = t < 0
        mask2 = t > 1
        numpy.subtract(p0, p, where=~(mask1 | mask2), out=dist)
        numpy.subtract(p1, p, where=mask1, out=dist)
        numpy.subtract(p2, p, where=mask2, out=dist)
    else:
        dist = p0 - p
    dist = numpy.square(dist, out=dist).sum(axis=axis, keepdims=True)
    numpy.sqrt(dist, out=dist)

    if axis is None or seg.ndim == 1:
        dist = dist.item()
        t = t.item()
    else:
        dist = dist.squeeze(axis)
        t = t.squeeze(axis)

    if return_t:
        return dist, t
    return dist
