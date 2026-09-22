# -*- coding: utf-8 -*-
#
#   DIM-SDK : Decentralized Instant Messaging Software Development Kit
#
#                                Written in 2026 by Moky <albert.moky@gmail.com>
#
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

from typing import Optional, Union

from dimsdk import *
from dimax import MemoryCacheExtension


"""
    Format Conveniences
    ~~~~~~~~~~~~~~~~~~~~

    UTF-8, JSON, Hex, Base58, Base64, ...
"""


def base64_encode(data: bytes) -> str:
    return Base64.encode(data=data)


def base64_decode(string: str) -> Optional[bytes]:
    return Base64.decode(string=string)


def base58_encode(data: bytes) -> str:
    return Base58.encode(data=data)


def base58_decode(string: str) -> Optional[bytes]:
    return Base58.decode(string=string)


def hex_encode(data: bytes) -> str:
    return Hex.encode(data=data)


def hex_decode(string: str) -> Optional[bytes]:
    return Hex.decode(string=string)


def utf8_encode(string: str) -> bytes:
    return UTF8.encode(string=string)


def utf8_decode(data: bytes) -> Optional[str]:
    return UTF8.decode(data=data)


def json_encode(container: Union[StrMap, AnyList]) -> str:
    return JSON.encode(container=container)


def json_decode(string: str) -> Union[StrMap, AnyList, None]:
    return JSON.decode(string=string)


"""
    Extensions
    ~~~~~~~~~~
"""


def crypto_extensions() -> Union[CryptoExtensions,
                                 SymmetricKeyExtension, PublicKeyExtension, PrivateKeyExtension,
                                 GeneralCryptoExtension]:
    return shared_crypto_extensions


def format_extensions() -> Union[FormatExtensions,
                                 TransportableFileExtension,
                                 TransportableFileWrapperExtension]:
    return shared_format_extensions


def account_extensions() -> Union[AccountExtensions,
                                  AddressExtension, IDExtension, MetaExtension, DocumentExtension,
                                  MemoryCacheExtension, VisaAgentExtension, EncryptedBundleExtension,
                                  GeneralAccountExtension]:
    return shared_account_extensions


def message_extensions() -> Union[MessageExtensions,
                                  InstantMessageExtension, SecureMessageExtension, ReliableMessageExtension,
                                  MessagePackerExtension, MessageHandlerExtension,
                                  ContentExtension]:
    return shared_message_extensions


def command_extensions() -> Union[CommandExtension, GeneralCommandExtension]:
    return shared_message_extensions
