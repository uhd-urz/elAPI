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
# Version: 22 Jan 2022: Initial Coding

"""
Utilities for manipulating non-computational aspects of numpy arrays.

Mathematical computations belong in :py:mod:`haggis.math`.
"""

__all__ = [
    'find_peaks', 'isolate_dtype', 'iterate_dtype', 'map_array', 'mask2runs',
    'masked_index', 'prune_mask', 'replace_field', 'runs2mask', 'unmasked_index'
]


from itertools import product

import numpy

from . import Sentinel
from .numbers import digit_count


def isolate_dtype(dtype, char='O'):
    """
    Create a new dtype that only contains the fields and subfields
    of `dtype` matching primitive type given by letter `char`.

    The new dtype will be flat with N fields containing the
    offsets to the original elements of interest. It will have the
    same `itemsize` as `dtype`. Field names are not preserved.

    Parameters
    ----------
    dtype : numpy.dtype
        Data type to parse out
    char : str[1]
        Primitive type character code to search for

    Return
    ------
    isolated : dtype
        A dtype containing offsets to all instances of `char` in
        `dtype`.
    """
    def dfs(dtype, base):
        """
        A DFS search will be more likely to yield offsets in the
        correct order without sorting.

        Parameters
        ----------
        dtype :
            The root of the current branch.
        base :
            The offset of dtype within its parent.

        Return
        ------
        offsets :
            The list of offsets of matching primitive fields found
            so far.
        """
        # Structure
        if dtype.fields is not None:
            offsets = []
            for dt, offset in dtype.fields.values():
                offsets.extend(dfs(dt, base + offset))
            return offsets
        # Array
        elif dtype.subdtype is not None:
            offsets = dfs(dtype.subdtype[0], base)
            return list(
                (offsets + dtype.subdtype[0].itemsize *
                 numpy.arange(numpy.prod(dtype.shape))[:, None]).ravel()
            )
        # Primitive
        elif dtype.char == char:
            return [base]
        return []

    offsets = dfs(dtype, 0)
    n = len(offsets)
    k = digit_count(n)
    # Generate names
    names = [f'a{i + 1:0{k}d}' for i in range(n)]
    d = {'names': names, 'offsets': offsets,
         'formats': n * [char], 'itemsize': dtype.itemsize}
    return numpy.dtype(d)


def iterate_dtype(arr, iterate_elements=False, yield_key=False):
    """
    Generate each primitive sub-array of a complex datatype.

    The generator yields the array for each builtin dtype. The leading
    dimensions of each yielded array are `arr.shape` the trailing
    dimensions are determined by `iterate_elements` and the shapes
    present in each sub-dtype. Currently, only depth-first traversal is
    supported.

    An optional field key can be yielded as well, if `yield_key` is
    set. The key is a dot-separated string enumerating the visited
    fields. If `iterate_elements` is specified, it will contain
    bracketed indices as well. See the `Examples` section for more
    information, including a sample of the key format.

    Parameters
    ----------
    arr : numpy.ndarray
        Must have a `dtype` attribute.
    iterate_elements : bool
        If `True`, array elements of each dtype will be yielded
        separately. See `Examples` for more information.
    yield_key : bool
        Whether or not to generate a second output contatining the
        field key.

    Examples
    --------
    Create a complex dtype and an array of zeros::

        >>> dt0 = np.dtype([('a', np.float32), ('b', np.int32, 2)])
        >>> dt = np.dtype([('x', np.bool_), ('y', dt0, 3)])
        >>> arr = np.zeros((3, 3), dt)

    When iterating without elements, the genrator does not descend into
    each sub-dtype consisting of primitives::

        >>> for a, k in iterate_dtype(arr, yield_key=True):
        ...     print(k, a.dtype, a.shape)
        x bool (3, 3)
        y.a float32 (3, 3, 3)
        y.b int32 (3, 3, 3, 2)

    When `iterate_elements` is set, the generator descends into the
    elements of each sub-dtype, even if they are primitive::

        >>> for a, k in iterate_dtype(arr, iterate_elements=True, yield_key=True):
        ...     print(k, a.dtype, a.shape)
        x bool (3, 3)
        y[0].a float32 (3, 3)
        y[0].b[0] int32 (3, 3)
        y[0].b[1]int32 (3, 3)
        y[1].a float32 (3, 3)
        y[1].b[0] int32 (3, 3)
        y[1].b[1] int32 (3, 3)
        y[2].a float32 (3, 3)
        y[2].b[0] int32 (3, 3)
        y[2].b[1] int32 (3, 3)
    """
    def add(key, leaf, index=None):
        key = '{}.{}'.format(key, leaf) if key else leaf
        if index is not None:
            key = '{}[{}]'.format(key, ', '.join(map(str, index)))
        return key

    def pack(arr, key):
        if yield_key:
            return arr, key
        return arr

    if iterate_elements:
        def inner(arr, key):
            dt = arr.dtype
            if dt.fields is None:
                yield pack(arr, key)
            else:
                for fname, (ftype, _) in dt.fields.items():
                    if ftype.subdtype is not None:
                        for index in product(*(range(n) for n in ftype.shape)):
                            yield from inner(arr[fname][(Ellipsis,) + index],
                                             add(key, fname, index))
                    else:
                        yield from inner(arr[fname], add(key, fname))
    else:
        def inner(arr, key):
            dt = arr.dtype
            if dt.fields is None:
                yield pack(arr, key)
            else:
                for field in dt.fields:
                    yield from inner(arr[field], add(key, field))

    yield from inner(arr, '')


def replace_field(in_type, out_type, *fields, name=None):
    """
    Create a dtype that will allow viewing a subset of the fields of
    `in_type` with a different structure.

    This function preserves the names, types, and offsets of all the
    unmodified fields. The replacement type will cover the entirety of
    the named `fields`, regardless of whether the underlying fields are
    contiguous or not.

    If the size of the replaced block is a multiple of
    `out_type.itemsize` other than one, the output type will be an array.
    The multiple must be an integer.

    Parameters
    ----------
    in_type : numpy.dtype
        Datatype to transform.
    out_type : numpy.dtype
        Primitive types may be provided as the equivalent string or
        class object.
    *fields : str
        Names of the fields to transfrom. An empty `fields` means that
        all of them are to be replaced. A new field is generated as a
        contiguous block whose size must be a multiple of
        `out_type.itemsize`. All elements must be valid field names in
        `in_type`.
    name : str, optional
        The name of the replacement field. By default, this is just the
        concatenation of `fields`, respecting CamelCase and snake_case
        conventions in transitions.

    Returns
    -------
    dtype :  numpy.dtype
        Dtype with the named `fields` replaced by a scalar or array of
        `out_type`. All other fields remain the same.

    Examples
    --------
    A simple case:

        >>> inner = np.dtype([('Roll', np.float32),
        ...                   ('Pitch', np.float32),
        ...                   ('Yaw', np.float32)])
        >>> outer = np.dtype([('Position', np.float32, 3),
        ...                   ('Attitude', inner)])
        >>> replace_field(outer, np.float32, 'Attitude')
        dtype([('Position', '<f4', (3,)), ('Attitude', '<f4', (3,))])

    To modify nested custom types, call this function recursively::

        >>> replace_field(outer, replace_field(inner, np.float32), 'Attitude')
        dtype([('Position', '<f4', (3,)), ('Attitude', [('RollPitchYaw', '<f4', (3,))])])
    """
    if in_type.fields is None:
        raise ValueError(f'in_type must be structured dtype, found {in_type}')
    if any(f not in in_type.fields for f in fields):
        raise ValueError('in_type is missing some field(s): '
                         f'{", ".join(set(fields) - set(in_type.fields))}')
    out_type = numpy.dtype(out_type)

    if not fields:
        fields = in_type.fields.keys()
    if not name:
        names = []
        for field in fields:
            if (names and
                ((names[-1][-1].isalpha() ^ field[0].isalpha()) or
                 not (names[-1][-1].isupper() ^ field[0].isupper()))):
                names.append('_')
            names.append(field)
        name = ''.join(names)
    fields = set(fields)

    # Keep track of the elements to retain
    names = []
    formats = []
    offsets = []
    # Keep track of the index of the replacement in `keys`
    idx = None
    # Keep track of the min and max offsets covered
    start = stop = None

    # Generate the new dtype
    for field, (type, offset) in in_type.fields.items():
        if field in fields:
            if idx is None:
                idx = len(names)
                start = offset
                stop = offset + type.itemsize
            else:
                start = min(start, offset)
                stop = max(stop, offset + type.itemsize)
        else:
            names.append(field)
            formats.append(type)
            offsets.append(offset)

    n = (stop - start) // out_type.itemsize
    if out_type.itemsize * n != stop - start:
        raise ValueError(f'Specified block covers {stop - start} bytes, '
                         f'but replacement size is {out_type.itemsize}')

    names.insert(idx, name)
    formats.insert(idx, out_type if n == 1 else (out_type, n))
    offsets.insert(idx, start)
    return numpy.dtype({
        'names': names, 'formats': formats, 'offsets': offsets,
        'itemsize': in_type.itemsize
    })


def map_array(map, arr, value=None, default=Sentinel):
    """
    Convert the elements of a numpy array using a mapping.

    The implementation uses looping to interface between the python and
    numpy datasets, but is as efficient as possible under the
    circumstaces. Intended for mapping a small number of arbitrary
    labels to some alternative value.

    Parameters
    ----------
    map : Mapping
        The mapping to apply. Any object with a `get` method that
        supports default values is accepted.
    arr : array-like
        The array to convert.
    value : callable, optional
        A function to apply to the dictionary values before placing in
        the output array. The default is a no-op.
    default :
        The value to use for array elements not in `mapping`. The
        default is to raise a `KeyError`. `None` is interpreted as a
        valid default.

    Returns
    -------
    mapped_array : array-like
        An array of the same shape as `arr`, with elements transformed
        according to the mapping.
    """
    def get(key):
        v = map.get(key, default)
        if v is Sentinel:
            raise KeyError(key)
        return v

    unq, ind = numpy.unique(arr, return_inverse=True)
    if value:
        vals = [value(get(u)) for u in unq]
    else:
        vals = [get(u) for u in unq]
    return numpy.array(vals)[ind]


def mask2runs(mask, return_lengths=False, return_borders=False):
    """
    Find the runs in a boolean mask.

    Parameters
    ----------
    mask : array-like
        Boolean mask. If not boolean, will be cast to bool.
    return_lengths : bool, optional
        Whether or not to return an array of lengths for each run.
    return_borders : bool, optional
        Whether or not to return an array of dtype `np.int8` containing
        1 at each run start and -1 past run ends. The default is False.

    Returns
    -------
    regions : numpy.ndarray (N, 2)
        Array of indices for each run. First column is the location of
        the run start, second column is past the run end.
    lengths : numpy.ndarray (N)
        The length of each run. This is effectively
        ``regions[:, 1] - regions[:, 0]``. Only returned if
        `return_lengths` is `True`.
    borders : numpy.ndarray (mask.size + 1)
        Array of :py:obj:`numpy.int8` containing 1 at each run start,
        -1 past each run end, and zero elsewhere. Only returned if
        `return_borders` is `True`. Extends one element past the end of
        `mask`. ``np.cumsum(borders).view(bool)[:-1]`` is equivalent to
        `mask`.
    """
    mask = numpy.asanyarray(mask).astype(bool, copy=False)
    borders = numpy.diff(numpy.r_[numpy.int8(0),
                                  mask.view(numpy.int8),
                                  numpy.int8(0)])
    indices = numpy.flatnonzero(borders).reshape(-1, 2)

    if return_lengths:
        lengths = numpy.diff(indices, axis=1).ravel()
        if return_borders:
            return indices, lengths, borders
        return indices, lengths
    elif return_borders:
        return indices, borders
    return indices


def runs2mask(runs, n=None):
    """
    Convert an Nx2 array of run indices, such as the return of
    :py:func:`mask2runs` into a boolean mask of size `n`.

    Parameters
    ----------
    runs : array-like
        A two-column array, the first column being inclusive start
        indices for each run, and the second being exclusive stop
        indices.
    n : int, optional
        The size of the mask to generate. If missing (None), the
        end of the last run is assumed (``runs[-1, 1]``).

    Return
    ------
    mask : numpy.ndarray
        A boolean array of length ``n`` with runs set to True.
    """
    runs = numpy.asanyarray(runs)
    if n is None:
        n = runs[-1, 1]
    mask = numpy.zeros(n, dtype=bool)
    view = mask.view(numpy.int8)

    # Assign start indices
    view[runs[:, 0]] = 1

    # Assign end indices
    ends = runs[:, 1]
    if ends[-1] == n:
        ends = ends[:-1]
    view[ends] = -1

    numpy.cumsum(view, out=view)
    return mask


def prune_mask(mask, min_length=None, max_length=None, filter_func=None,
               return_runs=False, return_lengths=False, return_borders=False):
    """
    Prune the runs in `mask` to conform to some criteria.

    Parameters
    ----------
    mask : array-like
        Boolean mask. If not boolean, will be cast to bool.
    min_length : int, optional
        Runs shorter than this will be removed. Ignored if None.
    max_length : int, optional
        Runs longer than this will be removed. Ignored if None.
    filter_func : callable, optional
        Function that accepts an Nx2 array of runs, as from `mask2runs`,
        and returns an N-length boolean mask. True elements in the
        result will be retained, while False elements will be removed.
        Called after applying `min_length` and `max_length` constraints,
        if those are requested.
    return_runs : bool, optional
        Whether or not to return an Nx2 array of indices for the start
        (inclusive) and end (exclusive), of each run within the mask.
    return_lengths : bool, optional
        Whether or not to return an array of lengths for each retained
        run.
    return_borders : bool, optional
        Whether or not to return an array of dtype `np.int8` containing
        1 at each run start and -1 past run ends.

    Return
    ------
    pruned : numpy.ndarray[bool]
        Mask with any runs shorter than `min_length` and longer than
        `max_length` removed and `filter_func` applied to the remaining runs.
    runs : numpy.ndarray
        Nx2 array of remaining run indices, returned if `return_runs` is set.
        Same format as the result of `mask2runs`. Start index in the first
        column is inclusive, stop index in the second column is exclusive.
    lengths : numpy.ndarray
        N-element array of lengths of remaining runs, returned if
        `return_lengths` is set.
    borders : numpy.ndarray[numpy.int8]
        Array of the same size as `mask` containing 1 at the start of each run
        and -1 past the end, returned if `return_borders` is set. The sum of
        this array is the mask.
    """
    def len_mask(mask):
        nonlocal runs, lengths
        borders[runs[~mask, :]] = 0
        runs = runs[mask]
        lengths = lengths[mask]

    runs, lengths, borders = mask2runs(mask,
                                       return_lengths=True, return_borders=True)
    if min_length is not None:
        len_mask(lengths >= min_length)
    if max_length is not None:
        len_mask(lengths <= max_length)
    if filter_func is not None:
        len_mask(filter_func(runs))

    mask = numpy.cumsum(borders[:-1], out=borders[:-1]).view(bool)
    result = [mask]
    if return_runs:
        result.append(runs)
    if return_lengths:
        result.append(lengths)
    if return_borders:
        result.append(borders)
    if len(result) == 1:
        return mask
    return tuple(result)


def unmasked_index(index, mask):
    """
    Convert `index` in a masked aray into the corresponding index in the
    original.

    Given an array ``x`` of the same size as `mask`, determine the
    position of ``x[mask][index]`` in the original array ``x``. Since
    `mask` may be multi-dimensional but ``x[mask]`` is always raveled,
    the result may be a scalar or a tuple.

    Parameters
    ----------
    index : array-like[int]
        The index or indices into in the masked (raveled) array. Each
        element must be in
        ``[-np.count_nonzero(mask), np.count_nonzero(mask))``.
    mask : array-like[bool]
        A boolean mask to determine the indices of the array.
        Non-boolean mask arrays will be interpreted as booleans, as
        though with ``mask.astype(bool)``. Scalar arrays will be
        interpreted as one-element arrays, so scalar indexing 
        allowed.

    Return
    ------
    unmasked_index : int or numpy.ndarray or tuple
        If `mask` is a scalar or 1D, the result is the same size and
        shape as `index`. Otherwise, it is a tuple of length
        ``mask.ndim`` each of whose elements corresponds to a dimension,
        and it the same size and shape as `index``.
    """
    index = numpy.asanyarray(index)
    mask = numpy.asanyarray(mask)

    if index.size == 0:
        empty = numpy.array([], dtype=numpy.intp)
        return (empty,) * mask.ndim if mask.ndim > 1 else empty
    indices = numpy.argwhere(mask)
    if mask.ndim > 1:
        return tuple(indices.T[:, index])
    indices = indices[index].ravel()
    return indices if index.ndim else indices.item()


def masked_index(index, mask):
    """
    Convert N-dimensional `index` into its corresponding location in the
    masked array, if it is in the masked portion.

    Given an array ``x``, of the same size as `mask`, determine the
    position of ``x[index]`` in ``x[mask]``. If `index` is not in the
    masked portion, the corressponding output is set to ``-1``.

    Parameters
    ----------
    index : tuple
        The index or indices into the unmasked multi-dimensional array.
        A non-tuple (scalar or array) index may be used for 1D masks,
        will be wrapped in a tuple internally to avoid ambiguity. The
        number of elements in the tuple must match ``mask.ndim``, and
        all elements must all broadcast together.
    mask : array-like[bool]
        A boolean mask to determine the indices of the array.
        Non-boolean mask arrays will be interpreted as booleans, as
        though with ``mask.astype(bool)``. Scalar arrays will be
        interpreted as one-element arrays, so scalar indexing 
        allowed.

    Return
    ------
    masked_index : int or None
        If `index` corresponds to a `True` element of `mask`, return its
        position in the masked result. Otherwise, return `None`.
    """
    mask = numpy.asanyarray(mask, dtype=numpy.bool_)
    if not isinstance(index, tuple):
        index = (index,)
    if mask.ndim > 0 and mask.size > 0:
        if mask.ndim != len(index):
            raise ValueError('index must have length {}'.format(mask.ndim))
        # The following two lines are a hack until a new mode is added. See
        # https://github.com/numpy/numpy/issues/15475#issuecomment-1280056626
        index = tuple(numpy.asanyarray(i) for i in index)
        index = tuple(numpy.where(i < 0, i + s, i)
                            for i, s in zip(index, mask.shape))
        try:
            index = numpy.ravel_multi_index(index, mask.shape, mode='raise')
        except ValueError as e:
            raise IndexError(str(e))
    mask = mask.ravel()
    indices = mask.cumsum(dtype=numpy.intp)
    indices -= 1
    return numpy.where(mask[index], indices[index], numpy.intp(-1))


def find_peaks(arr, n_peaks=None, mode='value', return_values=False):
    """
    Find the locations of the `n_peaks` tallest or leftmost (unfiltered)
    local maxima of `arr`.

    When ``mode=='value'``, the first peak is located at
    ``arr.argmax()``. The second peak is the maximum value among the
    numbers that are not monotonically non-increasing away from the
    first peak. Successive peaks are returned from remaining portions
    of the array.

    For a plateau with multiple equal peak elements, only the first is
    returned. Similarly, if multiple peaks with the same values are
    found, they will be retreived in order of increasing index.

    Parameters
    ----------
    arr : array_like
        The data to search through. Expected to be 1D. Larger dimensions
        are raveled to avoid the problem of different numbers of results
        along a given axis.
    n_peaks : int or None
        The number of peaks to search for. None or negative searches for
        all available peaks. If `n_peaks` local maxima are not found,
        the result will be shorter than requested.
    mode : str
        One of {``'value'``, ``'index'``} (case insensitive):

        - ``'value'``: Return up to the first `n_peaks` tallest peaks,
          regardless of location.
        - ``'index'``: Return up to the first `n_peaks` local maxima,
          traversing the array from left to right, regardless of peak
          height.
    return_values : bool
        Return a second array containing the maximum values at each
        location. Convenience for ``arr[find_peaks(arr, ...)]``.

    Return
    ------
    peak_indices : numpy.ndarray[int]
        Locations of up to `n_peaks` local maxima. May be shorter than
        `n_peaks` if there are insufficient local maxima in the data.
    peak_values : numpy.ndarray
        Elements of `arr` at `peak_indices`.

    Notes
    -----
    To get peaks in reverse order with ``mode='index'``, reverse the
    input: ``arr[::-1]``.

    To get peaks sorted from left to right with ``mode='value'``, sort
    the results.
    """
    arr = numpy.asanyarray(arr).ravel()
    n = len(arr)
    if n_peaks is None:
        n_peaks = -1

    if not isinstance(mode, str):
        raise TypeError('mode must be one of the strings {{valid, index}}, '
                        'not {}'.format(type(mode).__name__))
    cmode = mode.casefold()

    indices = []
    if cmode == 'value':
        mask = numpy.ones(arr.shape, dtype=numpy.bool_)
        while n and len(indices) != n_peaks:
            index = unmasked_index(arr[mask].argmax(), mask)
            indices.append(index)
            # Find surrounding window
            start = mask[index::-1].argmin() # First zero before
            if start != 0:
                start = index - (start - 1)
            end = mask[index:].argmin()      # First zero after
            if end == 0:
                end = len(arr)
            else:
                end += index
            index -= start
            diff = numpy.diff(arr[start:end])
            zero = diff.dtype.type(0)
            # Find left side start of peak
            if index > 1:
                sstart = (diff[index - 1::-1] < zero).argmax()
                # If index is zero, entire left side is non-increasing
                if sstart != 0:
                    # Otherwise, adjust for reversal
                    sstart = index - sstart
            else:
                sstart = 0
            # Find right side end of peak
            if index < end - start - 2:
                send = (diff[index:] > zero).argmax()
                # If index is zero, entire right side is non-increasing
                if send != 0:
                    end = start + index + send + 1
            start += sstart
            mask[start:end] = False
            n -= end - start
    elif cmode == 'index':
        subset = arr
        offset = 0
        while n and len(indices) != n_peaks:
            if n == 1:
                index = 0
                end = 1
            else:
                diff = numpy.diff(subset)
                zero = diff.dtype.type(0)
                end = (diff < zero).argmax()
                if diff[end] >= 0:
                    # end == 0, since subset is constantly rising, set to last
                    end = n
                    index = n - 1
                else:
                    # Find beginning of plateau
                    index = (diff[end::-1] > zero).argmax()
                    # If index is zero, entire subset is plateau, leave it at 0
                    if index != 0:
                        # Otherwise, adjust for reversal
                        index = end - (index - 1)
            # Found a peak
            indices.append(index + offset)
            # Find end of trough
            if end < n - 2:
                end += (diff[end + 1:] > zero).argmax() + 1
                if diff[end] <= 0:
                    # Trough never ends
                    end = n
                else:
                    # Select first element of uptrend
                    end += 1
            else:
                end = n
            # Update subset
            offset += end
            n -= end
            subset = subset[end:]
    else:
        raise ValueError('mode must be one of {{valid, index}}, '
                         'not {}'.format(mode))

    indices = numpy.array(indices, dtype=numpy.intp)
    if return_values:
        return indices, arr[indices]
    return indices
