# -*- coding: utf-8 -*-
# ==============================================================================
# MIT License
#
# Copyright (c) 2019 Albert Moky
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

"""
    Utils
    ~~~~~

    I'm too lazy to write codes for demo project, so I borrow some utils here
    from the <dimsdk> packages, but I don't suggest you to do it also, because
    I won't promise these private utils will not be changed. Hia hia~ :P
                                             -- Albert Moky @ Jan. 23, 2019
"""

import traceback
from io import StringIO
from typing import TypeVar, Callable

from dimsdk.dkd.compress_keys import StringPairing

from dimap.crypto.aes import random_bytes
from dimax.mem import MemoryCache, ThanosCache

from small.utils import Singleton
from small.log import Log, Logging, LogLevel
from small.skywalker import Runnable, Runner, Daemon
from small.fsm import Delegate as StateDelegate

from aiou import Path, File, TextFile, JSONFile

from .sdk import *

from .checker import FrequencyChecker
from .checker import RecentTimeChecker

from .opt import SysArgvParser

from .log import init_logger

from .cache import CachePool, SharedCacheManager

from .http import HttpSession, HttpClient

from .conf_item import IConfig, MessageTransferAgent, Supervisor, NeighborLoader
from .config import Config


def template_replace(template: str, key: str, value: str) -> str:
    """ replace '{key}' with value """
    tag = '{%s}' % key
    return template.replace(tag, value)


def get_exception_traceback() -> str:
    buf = StringIO()
    traceback.print_exc(file=buf)
    return buf.getvalue()


T = TypeVar('T')


def list_remove_where(array: List[T], predicate: Callable[[T], bool]) -> List[T]:
    """
    Filters list in-place with two-pointer algorithm.
    Element will be removed if predicate returns True.

    :param array: Target list, modified in-place
    :param predicate: A function accepting an element, return True = remove, False = keep
    :return: The original input list (enables method chaining)
    """
    write = 0
    for item in array:
        if not predicate(item):
            array[write] = item
            write += 1
    del array[write:]
    return array


__all__ = [

    'StringPairing',

    'random_bytes',
    'MemoryCache', 'ThanosCache',

    'Singleton',
    'Log', 'Logging', 'LogLevel',
    'Runnable', 'Runner', 'Daemon',
    'StateDelegate',

    'Path', 'File', 'TextFile', 'JSONFile',

    # ================================================================

    'StrMap', 'MutableStrMap',
    'AnyList', 'StrList',

    'URI', 'DateTime',

    'Converter',

    # ----------------------------------------------------------------

    'MD5', 'MD5Digester',
    'SHA1', 'SHA1Digester',
    'md5', 'sha1', 'sha256', 'keccak256', 'ripemd160',

    'base64_encode', 'base64_decode', 'base58_encode', 'base58_decode',
    'hex_encode', 'hex_decode',
    'utf8_encode', 'utf8_decode',
    'json_encode', 'json_decode',

    'crypto_extensions', 'format_extensions',
    'account_extensions',
    'message_extensions', 'command_extensions',

    'is_before',
    'get_msg_sig', 'get_msg_info',

    # ================================================================

    'FrequencyChecker', 'RecentTimeChecker',

    'SysArgvParser',

    'init_logger',

    'CachePool', 'SharedCacheManager',

    'HttpSession', 'HttpClient',

    'IConfig', 'MessageTransferAgent', 'Supervisor', 'NeighborLoader',
    'Config',

    # ================================================================

    'template_replace',

    'get_exception_traceback',

    'list_remove_where',

]
