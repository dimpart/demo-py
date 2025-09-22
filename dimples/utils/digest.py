# -*- coding: utf-8 -*-
# ==============================================================================
# MIT License
#
# Copyright (c) 2020 Albert Moky
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
    Message Digest
    ~~~~~~~~~~~~~~

    MD5, SHA1, SHA-256, Keccak256, RipeMD-160, ...
"""

import hashlib

from dimsdk import MessageDigester


class MD5:
    digester: MessageDigester = None

    @classmethod
    def digest(cls, data: bytes) -> bytes:
        # assert MD5.digester is not None, 'MD5 coder not set yet'
        return cls.digester.digest(data=data)


class SHA1:
    digester: MessageDigester = None

    @classmethod
    def digest(cls, data: bytes) -> bytes:
        # assert SHA1.digester is not None, 'SHA1 coder not set yet'
        return cls.digester.digest(data=data)


class MD5Digester(MessageDigester):

    # Override
    def digest(self, data: bytes) -> bytes:
        """ MD5 digest """
        hash_obj = hashlib.md5()
        hash_obj.update(data)
        return hash_obj.digest()


class SHA1Digester(MessageDigester):

    # Override
    def digest(self, data: bytes) -> bytes:
        """ SHA1 Digest """
        return hashlib.sha1(data).digest()


#
#   Interfaces
#


def md5(data: bytes) -> bytes:
    return MD5.digest(data=data)


def sha1(data: bytes) -> bytes:
    return SHA1.digest(data=data)
