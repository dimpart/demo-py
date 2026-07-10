# -*- coding: utf-8 -*-
#
#   DIM-SDK : Decentralized Instant Messaging Software Development Kit
#
#                                Written in 2019 by Moky <albert.moky@gmail.com>
#
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
    Station & Service Provider (SP)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Station : DIM network server node
    SP      : DIM network service provider
"""

from typing import Optional, List, Set

from dimsdk import Converter, EncryptedBundle

from dimsdk import ANYWHERE, EVERYWHERE
from dimsdk import EntityType, ID, Identifier
from dimsdk import Meta, Document, Visa

from dimsdk import User, UserDataSource
from dimsdk import BaseUser
from dimsdk import BaseGroup

from .utils import DocumentUtils


class Station(User):

    ANY = Identifier.new(name='station', address=ANYWHERE)
    EVERY = Identifier.new(name='stations', address=EVERYWHERE)

    def __init__(self, identifier: ID = None, host: str = None, port: int = 0):
        super().__init__()
        if identifier is None:
            identifier = self.ANY
        else:
            assert identifier.type == EntityType.STATION, 'Station ID type error: %s' % identifier
        self.__user = BaseUser(identifier=identifier)
        self.__host = host
        self.__port = port
        self.__isp: Optional[ID] = None

    # Override
    def __str__(self) -> str:
        """ Return str(self). """
        clazz = self.__class__.__name__
        identifier = self.identifier
        network = identifier.address.network
        return '<%s id="%s" network=%d host="%s" port=%d />' % (clazz, identifier, network, self.host, self.port)

    # Override
    def __eq__(self, other) -> bool:
        """ Return self==value. """
        if isinstance(other, Station):
            # check ID, host & port
            return same_stations(self, other)
        # check with inner user's ID
        return self.__user == other

    # Override
    def __ne__(self, other) -> bool:
        """ Return self!=value. """
        if isinstance(other, Station):
            # check ID, host & port
            return not same_stations(self, other)
        # check with inner user's ID
        return self.__user != other

    # Override
    def __hash__(self) -> int:
        return hash(self.__user)

    async def reload(self):
        """ Reload station info: host & port, SP ID """
        doc = await self.profile
        if doc is not None:
            host = doc.get_property(name='host')
            host = Converter.get_str(value=host)
            if host is not None:
                self.__host = host
            port = doc.get_property(name='port')
            port = Converter.get_int(value=port)
            if port is not None and port > 0:
                assert 16 < port < 65536, 'station port error: %d' % port
                self.__port = port
            isp = doc.get_property(name='provider')
            isp = ID.parse(identifier=isp)
            if isp is not None:
                self.__isp = isp

    @property
    async def profile(self) -> Optional[Document]:
        """ Station Document """
        docs = await self.documents
        return DocumentUtils.last_document(documents=docs)

    #
    #   Server
    #

    @property
    def host(self) -> Optional[str]:
        """ Station IP """
        return self.__host

    @property
    def port(self) -> int:
        """ Station Port """
        return self.__port

    @property
    def provider(self) -> Optional[ID]:
        """ ISP ID, station group """
        return self.__isp

    #
    #   Entity
    #

    @property  # Override
    def identifier(self) -> ID:
        return self.__user.identifier

    @identifier.setter
    def identifier(self, sid: ID):
        user = BaseUser(identifier=sid)
        user.data_source = self.data_source
        self.__user = user

    @property  # Override
    def type(self) -> int:
        return self.__user.type

    @property  # Override
    def data_source(self) -> Optional[UserDataSource]:
        return self.__user.data_source

    @data_source.setter  # Override
    def data_source(self, delegate: UserDataSource):
        self.__user.data_source = delegate

    @property  # Override
    async def meta(self) -> Meta:
        return await self.__user.meta

    @property  # Override
    async def documents(self) -> List[Document]:
        return await self.__user.documents

    #
    #   User
    #

    @property  # Override
    async def contacts(self) -> List[ID]:
        return await self.__user.contacts

    @property  # Override
    async def terminals(self) -> Set[str]:
        return await self.__user.terminals

    # Override
    async def verify(self, data: bytes, signature: bytes) -> bool:
        return await self.__user.verify(data=data, signature=signature)

    # Override
    async def encrypt_bundle(self, plaintext: bytes) -> EncryptedBundle:
        return await self.__user.encrypt_bundle(plaintext=plaintext)

    # Override
    async def sign(self, data: bytes) -> bytes:
        return await self.__user.sign(data=data)

    # Override
    async def decrypt_bundle(self, bundle: EncryptedBundle) -> Optional[bytes]:
        return await self.__user.decrypt_bundle(bundle=bundle)

    # Override
    async def sign_visa(self, visa: Visa) -> Visa:
        return await self.__user.sign_visa(visa=visa)

    # Override
    async def verify_visa(self, visa: Visa) -> bool:
        return await self.__user.verify_visa(visa=visa)


class ServiceProvider(BaseGroup):

    # default service provider
    GSP = Identifier.new(name='gsp', address=EVERYWHERE)

    def __init__(self, identifier: ID):
        super().__init__(identifier=identifier)
        assert identifier.type == EntityType.ISP, 'Service Provider ID type error: %s' % identifier

    @property
    async def profile(self) -> Optional[Document]:
        """ Provider Document """
        docs = await self.documents
        return DocumentUtils.last_document(documents=docs)

    @property
    async def stations(self) -> List:
        doc = await self.profile
        if doc is not None:
            array = doc.get_property(name='stations')
            if isinstance(array, List):
                return array
        # TODO: load from local storage
        return []

#
#   Comparison
#


def same_stations(a: Station, b: Station) -> bool:
    if a is b:
        # same object
        return True
    else:
        return check_identifiers(a.identifier, b.identifier) and \
               check_hosts(a.host, b.host) and \
               check_ports(a.port, b.port)


def check_identifiers(a: ID, b: ID) -> bool:
    if a is b:
        # same object
        return True
    elif a.is_broadcast or b.is_broadcast:
        return True
    else:
        return a == b


def check_hosts(a: Optional[str], b: Optional[str]) -> bool:
    if a is None or b is None:
        return True
    elif len(a) == 0 or len(b) == 0:
        return True
    else:
        return a == b


def check_ports(a: Optional[int], b: Optional[int]) -> bool:
    if a is None or b is None:
        return True
    elif a == 0 or b == 0:
        return True
    else:
        return a == b
