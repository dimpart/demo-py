# -*- coding: utf-8 -*-
#
#   DIM-SDK : Decentralized Instant Messaging Software Development Kit
#
#                                Written in 2022 by Moky <albert.moky@gmail.com>
#
# ==============================================================================
# MIT License
#
# Copyright (c) 2022 Albert Moky
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

from abc import ABC, abstractmethod
from typing import Optional, Dict

from dimsdk import ReliableMessage
from dimsdk import shared_message_extensions

from ....common import CustomizedContent

from .handler import CustomizedContentHandler
from .handler import BaseCustomizedContentHandler


class CustomizedContentFilter(ABC):

    @abstractmethod
    def filter_content(self, content: CustomizedContent, msg: ReliableMessage) -> CustomizedContentHandler:
        raise NotImplementedError(
            f'Not implemented: {type(self).__module__}.{type(self).__name__}.filter_content()'
        )


class AppCustomizedFilter(CustomizedContentFilter):

    def __init__(self):
        super().__init__()
        self.__default_handler = BaseCustomizedContentHandler()
        self.__handlers: Dict[str, CustomizedContentHandler] = {}

    def set_content_handler(self, app: str, mod: str, handler: CustomizedContentHandler):
        key = '%s:%s' % (app, mod)
        self.__handlers[key] = handler

    # protected
    def get_content_handler(self, app: str, mod: str) -> Optional[CustomizedContentHandler]:
        key = '%s:%s' % (app, mod)
        return self.__handlers.get(key)

    # Override
    def filter_content(self, content: CustomizedContent, msg: ReliableMessage) -> CustomizedContentHandler:
        # app = content.application
        app = content.get_str(key='app', default='')
        mod = content.module
        handler = self.get_content_handler(app=app, mod=mod)
        if handler is not None:
            return handler
        # if the application has too many modules, I suggest you to
        # use different handler to do the jobs for each module.
        return self.__default_handler


# -----------------------------------------------------------------------------
#  Message Extensions
# -----------------------------------------------------------------------------


class CustomizedFilterExtension:

    @property
    def customized_filter(self) -> CustomizedContentFilter:
        raise NotImplementedError(
            f'Not implemented: {type(self).__module__}.{type(self).__name__}.customized_filter getter'
        )

    @customized_filter.setter
    def customized_filter(self, delegate: CustomizedContentFilter):
        raise NotImplementedError(
            f'Not implemented: {type(self).__module__}.{type(self).__name__}.customized_filter setter'
        )


shared_message_extensions.customized_filter = AppCustomizedFilter()


def customized_extensions() -> CustomizedFilterExtension:
    return shared_message_extensions


def get_app_filter() -> AppCustomizedFilter:
    ext = customized_extensions()
    customized_filter = ext.customized_filter
    if not isinstance(customized_filter, AppCustomizedFilter):
        customized_filter = AppCustomizedFilter()
        ext.customized_filter = customized_filter
    return customized_filter
