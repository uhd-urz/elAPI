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
Custom module loading functionality for Python code, wrapped around
portions of :py:mod:`importlib`.
"""

__all__ = ['load_object', 'load_module', 'module_as_dict']


from collections import deque
from importlib import import_module
from importlib.util import spec_from_loader, module_from_spec
from importlib.machinery import SourceFileLoader
from inspect import ismodule, isclass, isfunction
from os.path import basename, splitext
import sys


def load_object(name):
    """
    Imports a single object by its qualified name.

    `name` is expected to have the form ``pkg.module.object``, with all
    elements separated by dots. The last element is the name of the
    module-level attribute to load. The path is expected to be
    accessible from the normal Python path.
    """
    path = name.split('.')
    name = path[-1]
    path = '.'.join(path[:-1])
    module = import_module(path)
    return getattr(module, name)


def load_module(module, name=None, sys_module=False,
                injection_var=None, injection=None):
    """
    Load a module from a text file containing Python code.

    Parameters
    ----------
    module : str or pathlib.Path
        The path of the file to load.
    name : str or None
        The name under which the module is imported (its `__name__`
        attribute). If not supplied, or a falsy value, the name is
        computed from the file name, minus the extension. Setting this
        parameter to ``'__main__'`` will trigger import guards.
    sys_module : bool
        If truthy, add the module to :py:obj:`sys.modules` under the
        correct name. Set this to `True` if importing files that
        contain relative imports. The default is `False`.
    injection :
        Any object that the user wishes to inject into the loading
        process. The object is visible to the code of the module
        under the name given by `injection_var`.
    injection_var : str or None
        The name of an attribute to inject into the loading process.
        The `injection` object is bound to this name the in the module
        namespace. The value of `injection` is never inspected. It is
        injected or omitted based solely on the contents of this
        parameter. A falsy value (the default) skips injection.
    """
    # Import module: taken from https://stackoverflow.com/a/67692/2988730
    mod_name = name if name else splitext(basename(module))[0]
    # str(module) necessary because import machinery does't accept Paths
    mod_spec = spec_from_loader(
        mod_name, loader=SourceFileLoader(mod_name, str(module))
    )
    mod = module_from_spec(mod_spec)
    if injection_var:
        # Keyword injection based on
        # https://stackoverflow.com/a/38650878/2988730
        mod.__dict__[injection_var] = injection
    if sys_module:
        # https://stackoverflow.com/a/50395128/2988730
        sys.modules[mod_spec.name] = mod
    mod_spec.loader.exec_module(mod)
    return mod


def module_as_dict(module, name=None, *, injection=None, injection_var=None,
                   recurse_injection=True, include_var='__include_files__',
                   skip_dunder=True, skip_modules=True, skip_classes=False,
                   skip_functions=False):
    """
    Load Python module code as a dictionary.

    This function is intended to support the loading of configuration
    files that use valid Python code into a dictionary. The loaded
    module will not be inserted into :py:data:`sys.modules`.

    Basic filtering of the loaded namespace is supported: dunder
    attributes and imported modules are omitted from the final result by
    default. This behavior can be altered with the `skip_dunder` and
    `skip_modules` parameters, respectively.

    A reference can be injected into the loaded module *before* its
    code is run (i.e., making it available to the module code) using
    the `injection` and `injection_var` parameters. `injection` is the
    data itself. It is never inspected or modified in any way.
    `injection_var` names the module attribute that `injection` will
    be bound to. If the module defines a variable with the same name as
    `injection_var`, the injected reference will have no effect.

    If a loaded module contains an attribute named by the
    `include_var` parameter, it must be a sequence of paths or
    strings. All names in the sequence will be loaded recursively into
    the same dictionary as well. Includes will be loaded and parsed with
    the same parameters as the root file (except for `name` and possibly
    `injection_var`), in breadth-first order. Successive levels do *not*
    override values set by the root module that this function is called
    with. In the model for which this function was developed,
    configuration files can reference and override default static
    configurations provided externally through include files.

    Parameters
    ----------
    module : str or pathlib.Path
        The path of the module to load.
    name : str or None
        The name under which the module is imported (its `__name__`
        attribute). If not supplied, or a falsy value, the name is
        computed from the file name, minus the extension. Setting this
        parameter to ``'__main__'`` will trigger import guards.
    injection :
        Any object that the user wishes to inject into the loading
        process. The object is visible to the code of the module
        under the name given by `injection_var`.
    injection_var : str or None
        The name of an attribute to inject into the loading process.
        The `injection` object is bound to this name the in the module
        namespace. The value of `injection` is never inspected. It is
        injected or omitted based solely on the contents of this
        parameter. A falsy value (the default) skips injection.
    recurse_injection : bool
        Whether or not to provide `injection` to recursively loaded
        modules (based on `include_var`). If recursion is enabled (the
        default), the same variable name is reused.
    include_var : str or None
        The name of the attribute to look into to find additional
        include files. Defaults to ``'__include_files__'``. If Falsy,
        do not recurse.
    skip_dunders : bool
        Whether or not to skip attributes starting with a double
        underscore (``__``) when converting to a dictionary. Defaults to
        :py:obj:`True`.
    skip_modules : bool
        Whether or not to skip module objects that are found in the
        loaded namespace when converting to a dictionary. Defaults to
        :py:obj:`True`.
    skip_classes : bool
        Whether or not to skip class objects that are found in the
        loaded namespace when converting to a dictionary. Defaults to
        :py:obj:`False`.
    skip_functions : bool
        Whether or not to skip function objects that are found in the
        loaded namespace when converting to a dictionary. Defaults to
        :py:obj:`False`.
    """
    def parse_module(mod, output, submodules):
        """
        Append the contents of the module's dictionary to an existing
        dictionary of key-value pairs.

        Modules and keys beginning with double underscore (``__``) can
        be filteres. Keys are *not* overriden in the output. Duplicates
        are discarded from the module being loaded and not overwritten.

        Parameters
        ----------
        mod : ModuleType
            The module to parse.
        output : dict
            The mutable dictionary to insert data into, constructed
            externally.
        submodules : deque
            A sequence of modules that are loaded as they are found in
            `include_var`. These modules will be parsed in the order
            found, maintaining the breadth-first contract.
        """
        # First extract the modules dictionary:
        mod = vars(mod)
        # Get the includes (so `skip_dunders` doesn't filter `include_var`)
        if include_var:
            inject = injection_spec if recurse_injection else {}
            submodules.extend(load_module(name, None, **inject)
                              for name in mod.get(include_var, []))

        # Create a filter method
        def filter_func(d, k, v):
            if k in d or (skip_dunder and k.startswith('__')):
                return False
            if ((skip_modules and ismodule(v)) or
                (skip_classes and isclass(v)) or
                (skip_functions and isfunction(v))):
                return False
            return True

        # Update the dictionary: use a generator for speed and efficiency
        dictionary.update(item for item in mod.items()
                          if filter_func(dictionary, *item))

    # Convert the module to a dictionary
    dictionary = {}
    submodules = deque()
    injection_spec = {'injection_var': injection_var, 'injection': injection}
    # Load the root module
    submodules.append(load_module(module, name, **injection_spec))

    # Keep adding elements to the dictionary as long as there are includes
    while submodules:
        parse_module(submodules.popleft(), dictionary, submodules)

    # Return the dictionary
    return dictionary
