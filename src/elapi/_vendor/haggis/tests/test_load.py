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
# Version: 27 Jan 2022: Initial Coding

"""
Tests for the :py:mod:`haggis.load` module.
"""


from os.path import abspath, dirname, join
import sys
from types import FunctionType, LambdaType, ModuleType

import pytest

from ..load import load_module, module_as_dict
from ..os import chdir_context


DATA_DIR = join(dirname(abspath(__file__)), 'data')


class Container:
    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)


class TestLoadModule:
    def setup_method(self):
        if 'module' in sys.modules:
            del sys.modules['module']

    def test_load(self):
        mod = load_module(join(DATA_DIR, 'module.txt'))
        assert mod.__name__ == 'module'
        assert hasattr(mod, 'a')
        assert hasattr(mod, 'b')
        assert hasattr(mod, 'c')
        assert hasattr(mod, '__d__')
        assert hasattr(mod, 'nested')
        assert 'module' not in sys.modules

    @pytest.mark.parametrize(('name', 'outname'),
            [(None, 'module'), ('', 'module'), ('testmodule', 'testmodule')])
    def test_name(self, name, outname):
        mod = load_module(join(DATA_DIR, 'module.txt'), name=name)
        assert mod.__name__ == outname
        assert hasattr(mod, 'a')
        assert hasattr(mod, 'b')
        assert hasattr(mod, 'c')
        assert hasattr(mod, '__d__')
        assert hasattr(mod, 'nested')
        assert outname not in sys.modules

    def test_sys(self):
        name = 'very_unlikely_test_module'
        assert name not in sys.modules
        try:
            mod = load_module(join(DATA_DIR, 'module.txt'), name=name, sys_module=True)
            assert mod.__name__ == name
            assert hasattr(mod, 'a')
            assert hasattr(mod, 'b')
            assert hasattr(mod, 'c')
            assert hasattr(mod, '__d__')
            assert hasattr(mod, 'nested')
            assert name in sys.modules
        finally:
            if name in sys.modules:
                del sys.modules[name]

    def test_injection(self):
        inject = Container(x=1)
        with pytest.raises(NameError):
            load_module(join(DATA_DIR, 'injection_module.txt'),
                        injection=inject, injection_var=None)

        mod = load_module(join(DATA_DIR, 'injection_module.txt'),
                          injection=inject, injection_var='injected')
        assert mod.injected is inject
        assert mod.a == 1


class TestModuleAsDict:
    def test_basic(self):
        config = module_as_dict(join(DATA_DIR, 'module.txt'))
        assert len(config) == 4
        assert config['a'] == 1
        assert isinstance(config['b'], FunctionType)
        assert isinstance(config['c'], type)
        assert '__d__' not in config
        assert 'e' not in config

    def test_include(self):
        with chdir_context(DATA_DIR):
            config = module_as_dict('module.txt', include_var='nested')
        assert len(config) == 5
        assert config['a'] == 1
        assert isinstance(config['b'], FunctionType)
        assert isinstance(config['c'], type)
        assert '__d__' not in config
        assert isinstance(config['d'], type)
        assert 'e' not in config
        

    def test_bfs(self):
        with chdir_context(DATA_DIR):
            config = module_as_dict('bfs_module_0.txt')
        assert len(config) == 4
        assert config['a'] == 1
        assert config['b'] == 2
        assert config['c'] == 3
        assert config['d'] == 42

    def test_skip_dunder(self):
        config = module_as_dict(join(DATA_DIR, 'module.txt'),
                                skip_dunder=False)
        assert config['a'] == 1
        assert isinstance(config['b'], FunctionType)
        assert isinstance(config['c'], type)
        assert isinstance(config['__d__'], LambdaType)
        assert 'e' not in config

    def test_skip_modules(self):
        config = module_as_dict(join(DATA_DIR, 'module.txt'),
                                skip_modules=False)
        assert len(config) == 5
        assert config['a'] == 1
        assert isinstance(config['b'], FunctionType)
        assert isinstance(config['c'], type)
        assert '__d__' not in config
        assert isinstance(config['e'], ModuleType)

    def test_skip_classes(self):
        config = module_as_dict(join(DATA_DIR, 'module.txt'),
                                skip_classes=True)
        assert len(config) == 3
        assert config['a'] == 1
        assert isinstance(config['b'], FunctionType)
        assert 'c' not in config
        assert '__d__' not in config
        assert 'e' not in config

    def test_skip_function(self):
        config = module_as_dict(join(DATA_DIR, 'module.txt'),
                                skip_functions=True, skip_dunder=False)
        assert config['a'] == 1
        assert 'b' not in config
        assert isinstance(config['c'], type)
        assert '__d__' not in config
        assert 'e' not in config

    def test_injection(self):
        with chdir_context(DATA_DIR):
            with pytest.raises(NameError):
                module_as_dict('injection_module.txt', include_var=None)
            with pytest.raises(AttributeError):
                module_as_dict('injection_module.txt',
                               injection_var='injected', include_var=None)
            config = module_as_dict('injection_module.txt',
                                    injection_var='injected',
                                    injection=Container(x=1),
                                    include_var=None)
            assert config['a'] == 1

    def test_recurse_injection(self):
        with chdir_context(DATA_DIR):
            with pytest.raises(NameError):
                module_as_dict('injection_module.txt',
                               injection=Container(x=1, y=2),
                               injection_var='injected',
                               recurse_injection=False)
            with pytest.raises(AttributeError):
                module_as_dict('injection_module.txt',
                               injection=Container(x=1),
                               injection_var='injected')
            config = module_as_dict('injection_module.txt',
                                    injection=Container(x=1, y=2),
                                    injection_var='injected')
            assert config['a'] == 1
            assert config['b'] == 2
