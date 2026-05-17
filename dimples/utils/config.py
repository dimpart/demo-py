# -*- coding: utf-8 -*-
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

from configparser import ConfigParser
from typing import Optional, List, Dict

from aiou import RedisConnector

from dimsdk import ID

from startrek.utils import Log, Logging

from .conf_item import IConfig
from .conf_item import MessageTransferAgent
from .conf_item import NeighborLoader


# @Singleton
class Config(IConfig, Logging):
    """ Config info from ini file """

    def __init__(self):
        super().__init__()
        self.__parser: Optional[ConfigParser] = None
        self.__ready = False
        self.__info = {}
        self.__path: Optional[str] = None
        self.__redis: Optional[RedisConnector] = None
        self.__stations: List[MessageTransferAgent] = []

    async def load(self, path: str = None):
        if path is None:
            path = self.__path
            assert path is not None, 'config file path not set yet'
            self.info(msg='reloading config: %s' % path)
        else:
            self.__path = path
            self.info(msg='loading config: %s' % path)
        parser = ConfigParser()
        parser.read(path)
        self.__parser = parser
        self.__ready = False
        self.__stations = None
        # load neighbor stations
        try:
            loader = NeighborLoader()
            self.__stations = await loader.load_stations(config=self)
        except Exception as error:
            self.error(msg='failed to load stations: %s, %s' % (error, parser))
        return self

    def to_dict(self) -> Optional[Dict]:
        parser = self.__parser
        if parser is None or self.__ready:
            return self.__info
        else:
            self.__ready = True
            return _update_sections(info=self.__info, parser=parser)

    # Override
    def __str__(self) -> str:
        return 'Config: %s' % self.to_dict()

    # Override
    def __repr__(self) -> str:
        return 'Config: %s' % self.to_dict()

    # Override
    def get_section(self, section: str) -> Optional[Dict]:
        parser = self.__parser
        if parser is not None:
            return _section_options(parser=parser, section=section)

    # Override
    def get_integer(self, section: str, option: str) -> int:
        parser = self.__parser
        if parser is None:
            return 0
        try:
            return parser.getint(section=section, option=option)
        except Exception as error:
            self.error(msg='failed to get integer: %s, %s, %s' % (section, option, error))
            return 0

    # Override
    def get_boolean(self, section: str, option: str) -> bool:
        parser = self.__parser
        if parser is None:
            return False
        try:
            return parser.getboolean(section=section, option=option)
        except Exception as error:
            self.error(msg='failed to get boolean: %s, %s, %s' % (section, option, error))

    # Override
    def get_string(self, section: str, option: str) -> Optional[str]:
        parser = self.__parser
        if parser is None:
            return None
        try:
            return parser.get(section=section, option=option)
        except Exception as error:
            self.error(msg='failed to get string : %s, %s, %s' % (section, option, error))

    # Override
    def get_list(self, section: str, option: str, separator: str = ',') -> Optional[List[str]]:
        """ get str and separate to a list """
        text = self.get_string(section=section, option=option)
        if text is None:
            return None
        result = []
        array = text.split(separator)
        for item in array:
            string = item.strip()
            if len(string) > 0:
                result.append(string)
        return result

    def get_identifier(self, section: str, option: str) -> Optional[ID]:
        value = self.get_string(section=section, option=option)
        return ID.parse(identifier=value)

    #
    #   database
    #

    @property
    def database_root(self) -> str:
        path = self.get_string(section='database', option='root')
        if path is None:
            return '/var/.dim'
        else:
            return path

    @property
    def database_public(self) -> str:
        path = self.get_string(section='database', option='public')
        if path is None:
            return '%s/public' % self.database_root     # /var/.dim/public
        else:
            return path

    @property
    def database_protected(self) -> str:
        path = self.get_string(section='database', option='protected')
        if path is None:
            return '%s/protected' % self.database_root  # /var/.dim/protected
        else:
            return path

    @property
    def database_private(self) -> str:
        path = self.get_string(section='database', option='private')
        if path is None:
            return '%s/private' % self.database_root    # /var/.dim/private
        else:
            return path

    #
    #   memory cache
    #

    @property
    def redis_connector(self) -> Optional[RedisConnector]:
        redis_enable = self.get_boolean(section='redis', option='enable')
        if not redis_enable:
            self.warning(msg='redis disabled')
            return None
        redis = self.__redis
        if redis is None:
            # create redis connector
            host = self.get_string(section='redis', option='host')
            if host is None:
                host = 'localhost'
            port = self.get_integer(section='redis', option='port')
            if port is None or port <= 0:
                port = 6379
            username = self.get_string(section='redis', option='username')
            password = self.get_string(section='redis', option='password')
            self.info(msg='enable redis://%s:%s@%s:%d' % (username, password, host, port))
            redis = RedisConnector(host=host, port=port, username=username, password=password)
            self.__redis = redis
        return redis

    #
    #   station
    #

    @property
    def station_id(self) -> Optional[ID]:
        return self.get_identifier(section='station', option='id')

    @property
    def station_host(self) -> Optional[str]:
        return self.get_string(section='station', option='host')

    @property
    def station_port(self) -> Optional[int]:
        return self.get_integer(section='station', option='port')

    #
    #   ans
    #

    @property
    def ans_records(self) -> Optional[Dict[str, str]]:
        return self.get_section(section='ans')

    #
    #   neighbor stations
    #
    @property
    def neighbors(self) -> List[MessageTransferAgent]:
        all_stations = self.__stations
        if all_stations is None:
            return []
        else:
            host = self.station_host
            port = self.station_port
            sid = self.station_id
        # remove myself
        neighbor_stations = []
        for station in all_stations:
            if station.identifier == sid:
                continue
            elif station.port == port and station.host == host:
                continue
            neighbor_stations.append(station)
        return neighbor_stations


def _update_sections(info: Dict, parser: ConfigParser) -> Dict:
    sections = parser.sections()
    for name in sections:
        options = _section_options(parser=parser, section=name)
        if options is None:
            options = {}
        info[name] = options
    return info


def _section_options(parser: ConfigParser, section: str) -> Optional[Dict]:
    try:
        array = parser.items(section=section)
    except Exception as error:
        Log.error(msg='failed to get section: %s, %s' % (section, error))
        return None
    # convert to dict
    options = {}
    for item in array:
        name = item[0]
        value = item[1]
        options[name] = value
    return options
