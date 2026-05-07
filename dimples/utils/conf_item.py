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

import weakref
from abc import ABC, abstractmethod
from typing import Optional, Any, Set, List, Dict
from typing import Iterable

from aiou import JSONFile

from dimsdk import JSON
from dimsdk import Dictionary
from dimsdk import EntityType, ID
from dimsdk import Facebook

from .log import Logging
from .http import HttpClient


class IConfig(ABC):

    @abstractmethod
    def get_section(self, section: str) -> Optional[Dict]:
        raise NotImplementedError('NotImplemented')

    @abstractmethod
    def get_integer(self, section: str, option: str) -> int:
        raise NotImplementedError('NotImplemented')

    @abstractmethod
    def get_boolean(self, section: str, option: str) -> bool:
        raise NotImplementedError('NotImplemented')

    @abstractmethod
    def get_string(self, section: str, option: str) -> Optional[str]:
        raise NotImplementedError('NotImplemented')

    @abstractmethod
    def get_list(self, section: str, option: str, separator: str = ',') -> Optional[List[str]]:
        raise NotImplementedError('NotImplemented')


class MessageTransferAgent(Dictionary):
    """ DIM Network Node """

    # Override
    def __str__(self) -> str:
        clazz = self.__class__.__name__
        return '<%s host="%s" port=%d id="%s" />' % (clazz, self.host, self.port, self.identifier)

    # Override
    def __repr__(self) -> str:
        clazz = self.__class__.__name__
        return '<%s host="%s" port=%d id="%s" />' % (clazz, self.host, self.port, self.identifier)

    @property
    def identifier(self) -> Optional[ID]:
        string = self.get(key='did')
        if string is None:
            string = self.get(key='ID')
        return ID.parse(identifier=string)

    @property
    def host(self) -> str:
        return self.get(key='host', default='')

    @property
    def port(self) -> int:
        return self.get(key='port', default=0)

    @classmethod
    def parse(cls, node: Any):
        if node is None:
            return None
        elif isinstance(node, MessageTransferAgent):
            return node
        elif isinstance(node, Dictionary):
            node = node.to_dict()
        host = node.get('host')
        port = node.get('port')
        if host is not None and port is not None and port > 0:
            return cls(dictionary=node)

    @classmethod
    def convert(cls, array: Iterable[Any]):
        stations = []
        for node in array:
            item = cls.parse(node=node)
            if item is not None:
                stations.append(item)
        return stations

    @classmethod
    def revert(cls, stations: Iterable) -> List[Dict]:
        array = []
        for node in stations:
            assert isinstance(node, MessageTransferAgent), 'station node error: %s' % node
            info = node.to_dict()
            array.append(info)
        return array


class Supervisor(Logging):
    """ System Administrators """

    def __init__(self, facebook: Facebook):
        super().__init__()
        self.__facebook = weakref.ref(facebook)

    @property
    def facebook(self) -> Optional[Facebook]:
        ref = self.__facebook
        if ref is not None:
            return ref()

    # noinspection PyMethodMayBeStatic
    def check_user(self, identifier: ID) -> bool:
        """ Filter user """
        return identifier.type == EntityType.USER

    # noinspection PyMethodMayBeStatic
    def get_identifiers(self, config: IConfig, section: str, option: str) -> List[ID]:
        """ Get ID list from config """
        array = config.get_list(section=section, option=option)
        return [] if array is None else ID.convert(array=array)

    async def get_users(self, config: IConfig, section: str = 'system', option: str = 'supervisors') -> Set[ID]:
        """ Get system administrators from config """
        all_users = set()
        array = self.get_identifiers(config=config, section=section, option=option)
        if array is None or len(array) == 0:
            return all_users
        facebook = self.facebook
        if facebook is None:
            # only filter user
            for item in array:
                if self.check_user(identifier=item):
                    all_users.add(item)
            return all_users
        # extract group members
        for item in array:
            if item.is_user:
                if self.check_user(identifier=item):
                    all_users.add(item)
                continue
            assert item.is_group, 'group ID error: %s' % item
            group_members = await facebook.get_members(identifier=item)
            if group_members is None or len(group_members) == 0:
                self.warning(msg='failed to get members for group: %s' % item)
                continue
            for member in group_members:
                if self.check_user(identifier=member):
                    all_users.add(member)
        return all_users


class NeighborLoader(Logging):

    def __init__(self):
        super().__init__()
        self.__http = HttpClient()

    async def load_stations(self, config: IConfig) -> Optional[List[MessageTransferAgent]]:
        # check remote URL
        source = config.get_string(section='neighbors', option='source')
        if source is None:
            stations = None
        else:
            stations = await self._download_stations(url=source)
        # check local path
        output = config.get_string(section='neighbors', option='output')
        if output is None:
            self.warning(msg='neighbors path not set')
        elif stations is None:
            stations = await self._load_stations(path=output)
        else:
            await self._save_stations(stations=stations, path=output)
        # OK
        return stations

    async def _download_stations(self, url: str) -> Optional[List[MessageTransferAgent]]:
        self.info(msg='downloading stations: %s' % url)
        http = self.__http
        try:
            response = http.cache_get(url=url)
            if response is None or response.status_code != 200:
                self.error(msg='failed to get URL: %s response: %s' % (url, response))
                return None
            else:
                text = response.text
                stations = JSON.decode(string=text)
        except Exception as error:
            self.error(msg='failed to download stations: %s, %s' % (error, url))
            return None
        if isinstance(stations, Dict):
            stations = stations.get('stations')
        if isinstance(stations, List):
            return MessageTransferAgent.convert(array=stations)

    async def _load_stations(self, path: str) -> Optional[List[MessageTransferAgent]]:
        self.info(msg='loading stations: %s' % path)
        try:
            stations = await JSONFile(path=path).read()
        except Exception as error:
            self.error(msg='failed to load stations: %s, %s' % (error, path))
            return None
        if isinstance(stations, Dict):
            stations = stations.get('stations')
        if isinstance(stations, List):
            return MessageTransferAgent.convert(array=stations)

    async def _save_stations(self, stations: List[MessageTransferAgent], path: str) -> bool:
        info = MessageTransferAgent.revert(stations=stations)
        self.info(msg='saving %d station(s): %s' % (len(stations), path))
        try:
            return await JSONFile(path=path).write(info)
        except Exception as error:
            self.error(msg='failed to save stations: %s, %s' % (error, path))
