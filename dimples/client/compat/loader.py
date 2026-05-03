# -*- coding: utf-8 -*-
# ==============================================================================
# MIT License
#
# Copyright (c) 2026 Albert Moky
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ==============================================================================

from dimplugins import ExtensionLoader, PluginLoader

from ...common.compat import CommonExtensionLoader, CommonPluginLoader
from ...common import GroupHistory

from ..cpu.app.filter import get_app_filter
from ..cpu import GroupHistoryHandler


class ClientLibraryLoader:

    def __init__(self, extensions: ExtensionLoader = None, plugins: PluginLoader = None):
        super().__init__()
        self.__extensions = ClientExtensionLoader() if extensions is None else extensions
        self.__plugins = CommonPluginLoader() if plugins is None else plugins
        self.__loaded = False

    def run(self):
        if self.__loaded:
            # no need to load it again
            return
        else:
            # mark it to loaded
            self.__loaded = True
        # try to load all plugins
        self.load()

    def load(self):
        self.__extensions.load()
        self.__plugins.load()


class ClientExtensionLoader(CommonExtensionLoader):

    # Override
    def load(self):
        super().load()
        self._register_customized_handlers()

    # noinspection PyMethodMayBeStatic
    def _register_customized_handlers(self):
        app_filter = get_app_filter()
        # 'chat.dim.group:history'
        app_filter.set_content_handler(app=GroupHistory.APP,
                                       mod=GroupHistory.MOD,
                                       handler=GroupHistoryHandler()
                                       )
