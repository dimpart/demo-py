# -*- coding: utf-8 -*-
# ==============================================================================
# MIT License
#
# Copyright (c) 2025 Albert Moky
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

from collections.abc import MutableMapping
from typing import Optional

from dimsdk import MessageCompressor
from dimsdk import MessageShortener

from ...utils import StrMap, MutableStrMap

from .compatible import CompatibleIncoming


class CompatibleCompressor(MessageCompressor):

    def __init__(self):
        super().__init__(shortener=CompatibleShortener())

    # # Override
    # def compress_content(self, content: StrMap, key: StrMap) -> bytes:
    #     # CompatibleOutgoing.fix_content(content=content);
    #     return super().compress_content(content=content, key=key)

    # Override
    def extract_content(self, data: bytes, key: StrMap) -> Optional[StrMap]:
        content = super().extract_content(data=data, key=key)
        if content is not None:
            if not isinstance(content, MutableMapping):
                content = dict(content)
            CompatibleIncoming.fix_content(content=content)
        return content


class CompatibleShortener(MessageShortener):

    # Override
    def compress_content(self, content: StrMap) -> StrMap:
        # DON'T COMPRESS NOW
        return content

    # Override
    def compress_symmetric_key(self, key: StrMap) -> StrMap:
        # DON'T COMPRESS NOW
        return key

    # Override
    def compress_reliable_message(self, msg: StrMap) -> StrMap:
        # DON'T COMPRESS NOW
        return msg

    # Override
    def extract_reliable_message(self, msg: StrMap) -> StrMap:
        if not isinstance(msg, MutableMapping):
            msg = dict(msg)
        msg = _fix_key(msg=msg)
        return super().extract_reliable_message(msg=msg)


def _fix_key(msg: MutableStrMap) -> StrMap:
    keys = msg.get('K')
    if keys is None:
        # assert 'data' in msg, f'message data should not empty: {msg}'
        pass
    elif isinstance(keys, dict):
        assert 'keys' not in msg, f'message keys duplicated: {msg}'
        msg.pop('K', None)
        # msg.pop('key', None)
        msg['keys'] = keys
    elif isinstance(keys, str):
        assert 'key' not in msg, f'message key duplicated: {msg}'
        msg.pop('K', None)
        # msg.pop('keys', None)
        msg['key'] = keys
    else:
        assert False, f'message key error: {msg}'
    # OK
    return msg
