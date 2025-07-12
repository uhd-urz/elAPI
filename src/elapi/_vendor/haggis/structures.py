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
# Version: 09 Jan 2021: Initial Coding

"""
Pure-python implementation of some useful data structures.
"""


__all__ = ['Trie']


from collections import deque
from itertools import chain
from os import sep
from os.path import isabs


class _TrieNode:
    """
    Contains information about a Node.

    This class has four slots:

    .. py:attribute:: key

       The key identifying this node.

    .. py:attribute:: parent

       A reference to the parent node for ease of traversal.

    .. py:attribute:: isleaf

       A boolean indicating whether this is a leaf or not. Since a leaf
       marks the end of a complete string, leaves can occur in the
       middle of a :py:class:`Trie` when a prefix is a valid string in
       its own right.

    .. py:attribute:: suffixes

       A mapping of suffix nodes prefixed by the current node, keyed by
       their :py:attr:`key` attribute. May be `None` to indicate an
       empty node.
    """
    __slots__ = ('key', 'parent', 'isleaf', 'suffixes')

    def __init__(self, key, parent, isleaf=False):
        """
        Initialize a new empty node.

        Inputs are copied directly, and :py:attr:`suffixes` is set to
        `None`.

        Parameters
        ----------
        key :
            The :py:attr:`key` to assign.
        parent : _TrieNode
            The :py:attr:`parent` node.
        isleaf : bool, optional
            The default :py:attr:`isleaf` is `False`.
        """
        self.key = key
        self.parent = parent
        self.isleaf = isleaf
        self.suffixes = None

    def __bool__(self):
        """
        The truth value of a node, used as a convenience when deleting
        nodes.

        Only nodes that are not leaves and empty are `False`. A root
        node, with a `None` parent, may not be `False`.
        """
        return self.isleaf or not self.isempty or self.parent is None

    def __str__(self):
        """
        Return a description of this node that will be used to display
        it as part of the entire structure.

        Returns
        -------
        str
            The key, followed by an asterisk if it is a leaf.
        """
        s = repr(self.key)
        if self.isleaf:
            s += '*'
        return s

    def __repr__(self):
        """
        Create a programatic description of this instance.

        Returns
        -------
        str
            A string that can be used to approximate a constructor call,
            with no information about suffixes.
        """
        return '{}(key={!r}, parent={}@{}, isleaf={})'.format(
                type(self).__name__, self.key, type(self.parent).__name__,
                id(self.parent), self.isleaf
        )

    def __len__(self):
        """
        The number of suffixes in this node.

        Returns
        -------
        int
            The number of child nodes.
        """
        return 0 if self.isempty else len(self.suffixes)

    def __contains__(self, key):
        """
        Check if the specified key is a valid suffix for this node.

        Parameters
        ----------
        key : str
            The key to check for.

        Returns
        -------
        bool
            `True` if this node has a suffix with the specified key,
            `False` otherwise.
        """
        return False if self.isempty else key in self.suffixes

    def __getitem__(self, key):
        """
        Retrieve a suffix node, creating it if necessary.

        This method accepts a single key: it is non-recursive.

        Parameters
        ----------
        key : str
            The key of the suffix to retrieve.

        Returns
        -------
        TrieNode
            The suffix node with the specified key. If necessary, a
            non-leaf node will be created for the given key, with
            this node set as the parent.
        """
        if self.isempty:
            self.suffixes = {}
        if key not in self.suffixes:
            self.suffixes[key] = type(self)(key, self)
        return self.suffixes[key]

    def __delitem__(self, key):
        """
        Remove the specified key from this node.

        Missing keys are silently ignored.

        Parameters
        ----------
        key : str
            The key corresponding to the suffix to remove. May be
            missing.
        """
        if key in self:
            if len(self.suffixes) == 1:
                self.suffixes = None
            else:
                del self.suffixes[key]

    @property
    def keylist(self):
        """
        Retrieves a list of all the suffix keys in this node.

        Read-only property.
        """
        if self.isempty:
            return []
        return list(self.suffixes.keys())

    @property
    def isempty(self):
        """
        `True` if this node has suffixes.

        Read-only property.
        """
        return self.suffixes is None

    @property
    def hierarchy(self):
        """
        Retrieve all the nodes between the root and this one.

        Read-only property.
        """
        p = []
        node = self
        while node is not None:
            p.append(node.key)
            node = node.parent
        return p[::-1]


class Trie:
    """
    Simple general purpose Trie implementation with methods for adding,
    removing, checking containment, and iterating.

    Root can be a leaf if the empty string is a prefix. Keys must be
    hashable.
    """
    __slots__ = ('root', 'len', 'sorter', 'joiner')

    def __init__(self, empty=None, sorter=None, joiner=None):
        """
        Make an empty trie.

        Do not delete existing data (e.g. if invoked multiple times).

        Parameters
        ----------
        empty : optional
            The key of the root node, associated with an empty trie.
            The default is `None`.
        sorter : callable, optional
            A callable that determines the sort order of suffixes
            during default iteration. If provided, must accept a list
            of keys and return an iterable. May filter the input by
            returning a subset. May be `None` (the default) to indicate
            no sorting on iteration. See :py:meth:`iter` for more
            information.
        joiner : callable, optional
            A callable that determines the concatenation of nodes
            during default iteration. If provided, must accept an
            iterable of keys and return the concatenated object. May
            be `None` (the default) to indicate no concatenation. See
            :py:meth:`iter` for more information.
        """
        if not hasattr(self, 'root'):
            self.root = _TrieNode(empty, None)
            self.len = 0
            self.sorter = (lambda x: x) if sorter is None else sorter
            self.joiner = tuple if joiner is None else joiner

    def add(self, item):
        """
        Add an item, represented as an iterable of parts.

        The last element of the iterable is marked as a leaf.

        Parameters
        ----------
        item :
            An iterable of keys. The last element will be marked as a
            leaf. An empty iterable refers to the root node.

        Returns
        -------
        bool
            `True` if a new leaf is added (even if it is prefix to an
            existing suffix), `False` if already a leaf.
        """
        node = self.root
        for elem in item:
            node = node[elem]
        if node.isleaf:
            return False
        self.len += 1
        node.isleaf = True
        return True

    def remove(self, item):
        """
        Remove an item, represented as an iterable of parts.

        If the leaf has a suffix, it is simply unmarked. If not, it, and
        its parents will be removed until a node with a different suffix
        or that is a leaf is encountered.

        Parameters
        ----------
        item :
            An iterable of keys. The last element will no longer be a
            leaf and may be deleted. An empty iterable refers to the
            root node.

        Returns
        -------
        bool
            `True` if the item was found and a node was removed, `False`
            if it did not represent a valid leaf.
        """
        node = self.root
        for elem in item:
            if elem not in node:
                return False
            node = node[elem]
        if node.isleaf:
            node.isleaf = False
            self.len -= 1
            while not node:
                del node.parent[node.key]
                node = node.parent
            return True
        return False

    def __len__(self):
        """
        Length is the number of leaf nodes, consistent with iteration.

        Returns
        -------
        int
            The number of leaves in this trie.
        """
        return self.len

    def __contains__(self, item):
        """
        Check if the specified item, represented as an iterable of
        parts, is a leaf of this trie.

        Parameters
        ----------
        item :
            An iterable of keys. The last element is checked for
            leafness. An empty iterable refers to the root node.

        Returns
        -------
        bool
            `True` if a the last element of `item` represents a leaf
            in the trie, `False` otherwise, even if it is a valid node.
        """
        node = self.root
        for elem in item:
            if not elem in node:
                return False
            node = node[elem]
        return node.isleaf

    def __iter__(self):
        """
        Default iterator over the leaf sequences.

        Iteration happens in deapth-first order. A customizable iterator
        is available through the :py:meth:`iter` method.
        """
        return self.iter()

    def iter(self, sorter=None, joiner=None, dfs=True):
        """
        Custom iterator over leaves of the trie.

        Parameters
        ----------
        sorter : callable or None
            If provided, used to sort the suffixes for each node.
            Otherwise, leaves will appear in insertion order (or none at
            all pre-Python 3.6). `sorter` must be a callable that
            accepts a list of keys and returns an iterable of keys. It
            can be used to filter elements as well as sort them.
        joiner : callable
            If provided, used to concatenate all the elements of each
            leaf. Otherwise, yield tuples with the elements. `joiner`
            must be a callable that accepts an iterable of keys and
            returns the concatenated object. The first element will always
            be the empty root key.
        dfs : bool
            Whether to perform breadth-first or depth-first-search. If
            `dfs` is False, a breadth-first order will be used rather
            than depth-first.
        """
        if sorter is None:
            sorter = self.sorter
        if joiner is None:
            joiner = self.joiner

        if dfs:
            def dfs_node(node):
                # Don't modify in place
                if node.isleaf:
                    yield node
                for key in sorter(node.keylist):
                    yield from dfs_node(node[key])
            yield from (joiner(node.hierarchy) for node in dfs_node(self.root))
        else:
            stack = deque([self.root])
            while stack:
                node = stack.popleft()
                if node.isleaf:
                    yield joiner(node.hierarchy)
                stack.extend(node[suffix] for suffix in sorter(node.keylist))

    def __repr__(self):
        """
        String representation of this trie.

        Returns
        -------
        str
            A multi-line description, with nodes indented to show
            hierarchy.
        """
        s = []
        def _repr(node, i):
            s.append(' ' * i + repr(node))
            for key in self.sorter(node.keylist):
                _repr(node[key], i + 2)
        _repr(self.root, 2)
        return '{}@{}{}{}'.format(type(self).__name__, id(self),
                                  '\n', '\n'.join(s))

    @classmethod
    def strings(cls):
        """
        Create a trie for strings.

        The root is an empty string, `sorter` is :py:func:`sorted`, and
        `jointer` is ``''.join``.

        Returns
        -------
        Trie
            A trie for strings.
        """
        return cls(empty='', sorter=sorted, joiner=''.join)

    @classmethod
    def string_paths(cls, sorter=sorted, joiner=None):
        """
        Create a trie for paths.

        Able to handle relative and absolute paths fairly well in the
        same trie,

        Parameters
        ----------
        sorter : callable, optional
            A replacement sorter. The default is :py:func:`sorted`, which
            implies case sensitivity.
        joiner : callable, optional
            A replacement joiner. The default joiner handles
            concatenation with the correct path separator, and proper
            identification of absolute and relative paths.

        Returns
        -------
        Trie
            A trie for paths.
        """
        if joiner is None:
            def joiner(parts):
                parts = iter(parts)
                root = next(parts)
                first = next(parts, None)
                if first is None:
                    return sep
                elif first == '.':
                    prefix = '.'
                elif isabs(first):
                    # Handle C:\\ on Windows
                    prefix = [first.rstrip('\\')]
                else:
                    prefix = [root, first]
                return sep.join(chain(prefix, parts))
        return cls(empty='', sorter=sorter, joiner=joiner)
