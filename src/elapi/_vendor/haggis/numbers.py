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
Various written-language related routines pertaining to numbers.
"""

__all__ = ['as_base', 'digit_count', 'english', 'metric_prefix']


from string import ascii_uppercase, digits as ascii_digits
from math import log, log10, ceil, floor
from operator import index


def as_base(n, base=10, letters=True, sign=True):
    """
    Convert integer `n` to representation as `base`.

    For bases 36 and under, digits 10 or larger can be represented by
    English letters in range A-Z. For larger bases, the output must be
    a list.

    Only absolute value of the number is coverted. For string
    representations, a ``-`` symbol can be prepended. Otherwise, it is
    the user's responsibility to handle sign.

    Parameters
    ----------
    n : int
        The number to represent.
    base : int
        The base of representation. Must be a positive integer.
        Special case of 1 is allowed.
    letters : bool, optional
        If True, represent digits larger than 9 with ASCII uppercase
        letters and return a string. If ``base > 36``, this parameter
        is ignored (implicitly False).
    sign : bool, optional
        Prepend a minus sign if returning a string and `n` is negative.
        Ignored if ``letters is False`` or ``base > 36``.

    Return
    ------
    num : str or list[int]
        If ``letters is True`` and ``base <= 36``, this is a string
        representation of `num` in `base` with optional sign.
        Otherwise, it is a list of digits from highest to lowest,
        ignoring sign.

    Notes
    -----
    Inspired by https://stackoverflow.com/a/28666223/2988730
    """
    base = int(base)
    if base < 1:
        raise ValueError('Illegal negative base')

    n = int(n) if isinstance(n, str) else index(n)
    if n < 0:
        s = True
        n = -n
    else:
        s = False

    if n == 0:
        digits = [0]
    elif base == 1:
        digits = [1] * abs(n)
    else:
        digits = []
        while n:
            digits.append(n % base)
            n //= base
        digits = digits[::-1]

    if base <= 36 and letters:
        digits = ''.join(ascii_uppercase[d - 10]
                                if d >= 10 else ascii_digits[d]
                                       for d in digits)
        if sign and s:
            digits = '-' + digits

    return digits


def digit_count(n, base=10):
    """
    Compute the number of digits required to represent an integer in a
    given base, ignoring sign.

    All numbers have at least one digit except zero. The sign is
    removed when counting digits.

    Parameters
    ----------
    n : int
        A number.
    base : int
        The base to compute the digit count of `n` in.

    Return
    ------
    The number of digits in `n` when represented in `base`.

    Notes
    -----
    For string representations, count zero as a digit using::

        max(digit_count(n, base), 1)

    """
    n = index(n)
    base = index(base)
    if base == 1:
        return n
    return ceil(log(n + 1, base))


#: Written representation of numbers [0, 10).
_basic_ones = [
    'zero', 'one', 'two', 'three', 'four',
    'five', 'six', 'seven', 'eight', 'nine'
]

#: Written representation of numbers [10, 20).
_basic_teens = [
    'ten', 'eleven', 'twelve', 'thirteen', 'fourteen',
    'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen'
]

#: Written representation of multiples of ten less than 100.
_basic_tens = [
    'twenty', 'thirty', 'forty', 'fifty',
    'sixty', 'seventy', 'eighty', 'ninety',
]

#: Written representation of powers of thousands up to 10**63, based on
#: the short scale most common in modern English usage (no milliard or
#: billiard): https://en.wikipedia.org/wiki/Names_of_large_numbers
_basic_powers = [
    '', 'thousand', 'million', 'billion', 'trillion', 'quadrillion',
    'quintillion', 'sextillion', 'septillion', 'octillion', 'nonillion',
    'decillion', 'undecillion', 'duodecillion', 'tredecillion',
    'quattuordecillion', 'quindecillion', 'sexdecillion', 'septendecillion',
    'octodecillion', 'novemdecillion', 'vigintillion',
]

#: Special ordinals that are not just their written number suffixed by
#: ``-th``.
_ordinal_specials = {
    1: 'first', 2: 'second', 3: 'third', 5: 'fifth', 8: 'eighth', 9: 'ninth',
    12: 'twelfth',
}

#: Special suffixes for ordinals that are not just ``-th``.
_suffix_specials = {1: 'st', 2: 'nd', 3: 'rd',}

#: The default ordinal suffix is ``-th``.
_default_suffix = 'th'


def english(num, mode='basic', hyphens=True, one_is_a=False, format='d'):
    r"""
    Convert non-negative integer into its (mostly British) English
    equivalent.

    Integers up to 999 vigintillion (10\ :sup:`64` - 1) are supported.

    Usage is modifiable British as specced out in
    http://english.stackexchange.com/a/111837/207127.

    Optional hyphens can be turned off by setting `hyphens` to
    :py:obj:`False`.

    The more American prefix "one" is preferred when the highest power
    of 10 is a unit. True British usage can be enabled be setting
    `one_is_a` to :py:obj:`True`. This will make 100 translate as "a
    hundred" instead of the (default) Americanized "one hundred".

    Supported values for `mode` are:

      - ``'basic'``: Convert ``1`` into ``'one'``.
      - ``'ordinal'``: Convert ``1`` into ``'first'``.
      - ``'suffix'``: Convert ``1`` into ``'1st'``. Usage rules are
        irrelevant with this option.

    Usage of higher powers of 10 are Americanized as well:

      - 10\ :sup:`6`: million
      - 10\ :sup:`9`: billion
      - 10\ :sup:`12`: trillion
      - 10\ :sup:`15`: quadrillion
      - etc...

    `format` is an optional string that specifies an integer format
    conforming to the Python :ref:`formatspec` (used by
    :py:class:`string.Formatter` and :py:meth:`str.format`). The default
    is ``'d'``.
    """
    # Check that it is really an integer and non-negative
    num = int(num)
    if num < 0:
        raise ValueError('Only positive integers supported')

    # If need suffix, don't check range since everything > 20 is 'th'
    if mode == 'suffix':
        teens = num % 100
        if teens > 20:
            teens %= 10
        suffix = _suffix_specials.get(teens, _default_suffix)
        return '{:{}}{}'.format(num, format, suffix)

    if mode not in ('basic', 'ordinal'):
        raise ValueError('Unsupported mode "{}"'.format(mode))

    if num < 10:
        if mode == 'basic':
            return _basic_ones[num]
        return _ordinal_specials.get(num, _basic_ones[num] + _default_suffix)

    # Check range if not in suffix mode
    max_power = 3 * len(_basic_powers)
    # Originally tried to do log10(num) >= max_power. Didn't work because
    # log10(999999999999999999) == 18.0 due to limited precision of floats
    if num >= 10**max_power:
        raise ValueError('{} is out of range. Only numbers '
                         'up to 10**{} are supported.'.format(num, max_power))

    teen_sep = '-' if hyphens else ' '

    def separate(upper, lower, sep=' '):
        """
        Add the specified separator between two strings only if they are both
        non-empty.

        If either is empty, just returns the other one.
        """
        if upper and lower:
            return upper + sep + lower
        return upper + lower

    def process_thousand(num, use_a=False, add_suffix=False):
        """
        Convert the lowest three digits of a number into English
        format.

        This method does not process zero. If `top` is `True` and the
        number is either 1 or 100-199, the prefix will be 'a' instead
        of 'one'. Do not ask this method to process 1 if the entire
        number is 1.

        Ordinal mode can be handled here as well. If the suffix is
        requested, it is generated based on the last two digits if they
        are nonzero, added as 'th' if they are.
        """
        hundreds = num // 100
        if hundreds == 1 and use_a:
            upper = 'a hundred'
        elif hundreds:
            upper = _basic_ones[hundreds] + ' hundred'
        else:
            upper = ''

        def get_one(num):
            """
            Convert a number 0-9 to text.

            Zero becomes an empty string.
            """
            if num == 0:
                return ''
            if add_suffix:
                if num in _ordinal_specials:
                    return _ordinal_specials[num]
                return _basic_ones[num] + _default_suffix
            return _basic_ones[num]

        def get_teen(num):
            """ Convert a numbers 10-19 to text. """
            if add_suffix:
                if num in _ordinal_specials:
                    return _ordinal_specials[num]
                return _basic_teens[num - 10] + _default_suffix
            return _basic_teens[num - 10]

        def get_regular(num):
            """ Convert numbers 20-99 to text. """
            ones = num % 10
            base = _basic_tens[num // 10 - 2]
            if ones:
                return base + teen_sep + get_one(ones)
            else:
                if add_suffix:
                    return base[:-1] + 'ie' + _default_suffix
                return base

        teens = num % 100
        if teens == 1 and not hundreds and use_a:
            lower = 'a'
        elif teens < 10:
            lower = get_one(teens)
        elif teens < 20:
            lower = get_teen(teens)
        else:
            lower = get_regular(teens)

        return separate(upper, lower, ' and ')

    result = ''
    # Split number into groups of three digits. ceil(log1000(num + 1)) is the
    # total number of groups of 3 digits. The +1 ensures that exact powers of
    # 1000 get punted into the next group count. Also, it is not an issue that
    # this will not work correctly for zero since that special case is handled
    # above anyway.
    digit_list = [
        (num // 1000**n) % 1000 for n in range(int(ceil(log10(num + 1) / 3)))
    ]
    # What is the last index?
    max_index = len(digit_list) - 1
    # How much has been accumulated back
    total_so_far = 0
    for index, (power, digits) in enumerate(zip(_basic_powers, digit_list)):
        if digits:
            sep = ' and ' if total_so_far < 100 else ', '
            use_a = (bool(one_is_a) and index == max_index)
            add_suffix = (mode == 'ordinal' and total_so_far == 0)
            words = separate(process_thousand(digits, use_a, add_suffix), power)
            result = separate(words, result, sep)
        total_so_far += 1000**index * digits
    return result


#: Prefixes for the powers of 10 between -24 and +24:
#: https://en.wikipedia.org/wiki/Metric_prefix
_metric_prefixes = {
    24: ('Y', 'yotta'),
    21: ('Z', 'zetta'),
    18: ('E', 'exa'),
    15: ('P', 'peta'),
    12: ('T', 'tera'),
     9: ('G', 'giga'),
     6: ('M', 'mega'),
     3: ('k', 'kilo'),
     2: ('h', 'hecto'),
     1: ('da', 'deca'),
     0: ('', ''),
    -1: ('d', 'deci'),
    -2: ('c', 'centi'),
    -3: ('m', 'milli'),
    -6: ('μ', 'micro'),
    -9: ('n', 'nano'),
   -12: ('p', 'pico'),
   -15: ('f', 'femto'),
   -18: ('a', 'atto'),
   -21: ('z', 'zepto'),
   -24: ('y', 'yocto'),
}


def metric_prefix(num, long=False, eng=False):
    r"""
    Return a number and the letter that represents its metric prefix.

    Prefixes are recognized in powers of 10\ :sup:`3` between
    10\ :sup:`-24` and 10\ :sup:`24`. Prefixes for 10\ :sup:`-2`,
    10\ :sup:`-1`, 10\ :sup:`1` and 10\ :sup:`2` are also recognized if
    ``eng=False``.

    Known prefixes are given in the following table:

    +--------+--------+--------------+
    | Prefix | Symbol | Power of 10  |
    +========+========+==============+
    | yotta  | Y      |           24 |
    +--------+--------+--------------+
    | zetta  | Z      |           21 |
    +--------+--------+--------------+
    | exa    | E      |           18 |
    +--------+--------+--------------+
    | peta   | P      |           15 |
    +--------+--------+--------------+
    | tera   | T      |           12 |
    +--------+--------+--------------+
    | giga   | G      |            9 |
    +--------+--------+--------------+
    | mega   | M      |            6 |
    +--------+--------+--------------+
    | kilo   | k      |            3 |
    +--------+--------+--------------+
    | hecto  | h      |            2 |
    +--------+--------+--------------+
    | deca   | da     |            1 |
    +--------+--------+--------------+
    | <None> | <None> |            0 |
    +--------+--------+--------------+
    | deci   | d      |           -1 |
    +--------+--------+--------------+
    | centi  | c      |           -2 |
    +--------+--------+--------------+
    | milli  | m      |           -3 |
    +--------+--------+--------------+
    | micro  | μ      |           -6 |
    +--------+--------+--------------+
    | nano   | n      |           -9 |
    +--------+--------+--------------+
    | pico   | p      |          -12 |
    +--------+--------+--------------+
    | femto  | f      |          -15 |
    +--------+--------+--------------+
    | atto   | a      |          -18 |
    +--------+--------+--------------+
    | zepto  | z      |          -21 |
    +--------+--------+--------------+
    | yocto  | y      |          -24 |
    +--------+--------+--------------+

    Parameters
    ----------
    num : number
        The number to normalize
    long : bool
        Whether to return the prefix or just the symbol. Defaults to
        :py:obj:`False` (just the symbol).
    eng : bool
        Whether to use engineering notation (omit powers that aren't)
        multiples of 3. Deaults to :py:obj:`False`, so ``centi``,
        ``deca``, etc., are viable options.

    Return
    ------
    num : number
        The normalized number
    prefix : str
        One of the metric prefix strings. If `num` is already
        normalized, this is an empty string.
    factor : float
        A factor such that ``num * factor`` is the original input.
        If ``num`` is normalized, `factor` is 1.0.
    """
    power = floor(log10(abs(num)))
    if eng or power < -3 or power > 3:
        power = (power // 3) * 3
    prefix = _metric_prefixes[power][bool(long)]
    factor = 10**power
    return num / factor, prefix, factor
