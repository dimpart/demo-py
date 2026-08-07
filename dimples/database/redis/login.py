# -*- coding: utf-8 -*-
# ==============================================================================
# MIT License
#
# Copyright (c) 2021 Albert Moky
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

from typing import Optional, Tuple, List

from dimsdk import ID, ReliableMessage

from ...utils import json_encode, json_decode, utf8_encode, utf8_decode
from ...common import CommandMessageUtils
from ...common import LoginCommand

from .base import RedisCache


class LoginCache(RedisCache):

    # login info cached in Redis will be expired after 30 minutes, after that
    # it will be reloaded from local storage if it's still need.
    EXPIRES = 1800  # seconds

    @property  # Override
    def db_name(self) -> Optional[str]:
        return 'mkm'

    @property  # Override
    def tbl_name(self) -> str:
        return 'user'

    """
        Login info for Users
        ~~~~~~~~~~~~~~~~~~~~

        redis key: 'mkm.user.{ADDRESS}.login_commands'
    """
    def __login_cache_name(self, user: ID) -> str:
        address = str(user.address)
        return '%s.%s.%s.login_commands' % (self.db_name, self.tbl_name, address)

    async def save_login_command_messages(self, records: List[Tuple[LoginCommand, ReliableMessage]], user: ID) -> bool:
        """ cache login commands """
        info = CommandMessageUtils.dump_command_messages(records=records)
        js = json_encode(container=info)
        value = utf8_encode(string=js)
        name = self.__login_cache_name(user=user)
        # self.info('Caching %d record(s) for key: %s', len(records), name)
        return await self.set(name=name, value=value, expires=self.EXPIRES)

    async def load_login_command_messages(self, user: ID) -> Optional[List[Tuple[LoginCommand, ReliableMessage]]]:
        """ load login commands from cache """
        name = self.__login_cache_name(user=user)
        value = await self.get(name=name)
        if value is None:
            # not found
            return None
        js = utf8_decode(data=value)
        assert js is not None, f'failed to decode string: {value}'
        info = json_decode(string=js)
        # load login records from cache server
        return CommandMessageUtils.pump_command_messages(info=info)
