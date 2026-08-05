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
from typing import Optional, List

from dimsdk.core.compress_keys import StringPairing
from dimsdk import *

from dimplugins.crypto.aes import random_bytes
from dimplugins.mem import MemoryCache, ThanosCache

from startrek.utils import Log, Logging, LogLevel
from startrek.skywalker import Singleton
from startrek.skywalker import Runnable, Runner, Daemon
from startrek.fsm import Delegate as StateDelegate

from aiou import Path, File, TextFile, JSONFile

from .digest import md5, sha1

from .checker import FrequencyChecker
from .checker import RecentTimeChecker

from .opt import SysArgvParser

from .log import init_logger
from .cache import CachePool, SharedCacheManager

from .http import HttpSession, HttpClient

from .conf_item import IConfig, MessageTransferAgent, Supervisor, NeighborLoader
from .config import Config


def is_before(old_time: Optional[DateTime], new_time: Optional[DateTime]) -> bool:
    """ check whether new time is before old time """
    if old_time is None or new_time is None:
        return False
    else:
        return new_time.before(old_time)
    # return DocumentUtils.is_before(old_time, new_time)


def get_msg_sig(msg: ReliableMessage, size: int = -1) -> str:
    """ last 6 bytes (signature in base64) """
    sig = msg.get('signature')
    # assert isinstance(sig, str), f'signature error: {sig}'
    sig = sig.strip()
    if size < 0:
        return sig
    assert 0 < size < len(sig)
    return sig[-size:]  # last 6 bytes (signature in base64)


def get_msg_traces(msg: ReliableMessage) -> List:
    traces = msg.get('traces')
    if traces is None:
        return []
    assert isinstance(traces, list), f'traces error: {traces}'
    stations = []
    for item in traces:
        if isinstance(item, dict):
            sid = item.get('did')
            if sid is None:
                sid = item.get('ID')
        elif isinstance(item, str):
            sid = item
        else:
            Log.error('trace item error: %s', item)
            continue
        stations.append(sid)
    return stations


def get_msg_info(msg: ReliableMessage) -> str:
    sender = msg.sender
    receiver = msg.receiver
    rcpt = msg.get('rcpt')
    group = msg.group
    # traces
    traces = get_msg_traces(msg=msg)
    sig = get_msg_sig(msg=msg, size=8)
    if group is None:
        return f'type={msg.type}, "{sig}" [{msg.time}] {sender} => {receiver} ({rcpt}), traces: {traces}'
    else:
        return f'type={msg.type}, "{sig}" [{msg.time}] {sender} => {receiver} ({rcpt}), group={group}, traces: {traces}'


def template_replace(template: str, key: str, value: str) -> str:
    """ replace '{key}' with value """
    tag = '{%s}' % key
    return template.replace(tag, value)


def get_exception_traceback() -> str:
    buf = StringIO()
    traceback.print_exc(file=buf)
    return buf.getvalue()


__all__ = [

    'md5', 'sha1', 'sha256', 'keccak256', 'ripemd160',
    'base64_encode', 'base64_decode', 'base58_encode', 'base58_decode',
    'hex_encode', 'hex_decode',
    'utf8_encode', 'utf8_decode',
    'json_encode', 'json_decode',

    'random_bytes',
    'MemoryCache', 'ThanosCache',

    'StrMap', 'MutableStrMap',
    'AnyList', 'StrList',

    'StringPairing',

    'URI', 'DateTime',

    'Converter',

    'Runnable', 'Runner', 'Daemon',
    'StateDelegate',


    'Singleton',

    'SysArgvParser',

    'Log', 'Logging', 'LogLevel',
    'init_logger',

    'Path', 'File', 'TextFile', 'JSONFile',
    'CachePool', 'SharedCacheManager',

    'HttpSession', 'HttpClient',

    'FrequencyChecker', 'RecentTimeChecker',

    'IConfig', 'MessageTransferAgent', 'Supervisor', 'NeighborLoader',
    'Config',

    'is_before',
    'get_msg_sig', 'get_msg_info',
    'template_replace',

    'get_exception_traceback',

]
