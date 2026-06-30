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

import threading
from typing import Optional, Tuple, List

from aiou.mem import CachePool

from dimsdk import ID
from dimsdk import ReliableMessage

from ..utils import Config
from ..utils import naked_id, dressed_id
from ..utils import is_before
from ..common import LoginDBI, LoginCommand

from .dos import LoginStorage
from .redis import LoginCache

from .t_base import DbTask, DataCache


class CmdTask(DbTask[ID, List[Tuple[LoginCommand, ReliableMessage]]]):

    def __init__(self, user: ID,
                 redis: LoginCache, storage: LoginStorage,
                 mutex_lock: threading.Lock, cache_pool: CachePool):
        super().__init__(mutex_lock=mutex_lock, cache_pool=cache_pool)
        self._user = user
        self._redis = redis
        self._dos = storage

    @property  # Override
    def cache_key(self) -> ID:
        return self._user

    # Override
    async def _read_data(self) -> Optional[List[Tuple[LoginCommand, ReliableMessage]]]:
        # 1. the redis server will return None when cache not found
        # 2. when redis server return a tuple with None values, no need to check local storage again
        array = await self._redis.load_login_command_messages(user=self._user)
        if len(array) > 0:
            return array
        # 3. the local storage will return a tuple with None values, when command not found
        array = await self._dos.load_login_command_messages(user=self._user)
        if array is None:
            # 4. return a tuple with None values as a placeholder for the memory cache
            array = []
        # 5. update redis server
        await self._redis.save_login_command_messages(records=array, user=self._user)
        return array

    # Override
    async def _write_data(self, records: List[Tuple[LoginCommand, ReliableMessage]]) -> bool:
        # 1. store into redis server
        ok1 = await self._redis.save_login_command_messages(records=records, user=self._user)
        # 2. save into local storage
        ok2 = await self._dos.save_login_command_messages(records=records, user=self._user)
        return ok1 or ok2


class LoginTable(DataCache, LoginDBI):
    """ Implementations of LoginDBI """

    def __init__(self, config: Config):
        super().__init__(pool_name='login')  # ID => (LoginCommand, ReliableMessage)
        self._redis = LoginCache(config=config)
        self._dos = LoginStorage(config=config)

    def show_info(self):
        self._dos.show_info()

    def _new_task(self, user: ID) -> CmdTask:
        return CmdTask(user=user,
                       redis=self._redis, storage=self._dos,
                       mutex_lock=self._mutex_lock, cache_pool=self._cache_pool)

    async def _load_login_command_messages(self, user: ID) -> List[Tuple[LoginCommand, ReliableMessage]]:
        task = self._new_task(user=user)
        array = await task.load()
        return [] if array is None else array

    #
    #   Login DBI
    #

    # Override
    async def save_login_command_message(self, user: ID, content: LoginCommand, msg: ReliableMessage) -> bool:
        new_time = content.time
        terminal = content.get_str(key='terminal')
        if terminal is None or len(terminal) == 0:
            terminal = user.terminal
        target = ID.create(name=user.name, address=user.address, terminal=terminal)
        naked = naked_id(did=user)
        records = await self._load_login_command_messages(user=naked)
        #
        #  check command time
        #
        updated = False
        index = len(records)
        while index > 0:
            index -= 1
            old_cmd, old_msg = records[index]
            if not isinstance(old_cmd, LoginCommand):
                self.error('login command error: %s, %s', user, old_cmd)
                continue
            old_id = old_cmd.identifier
            old_ter = old_cmd.get_str(key='terminal')
            if dressed_id(did=old_id, terminal=old_ter) != target:
                self.warning('skip login command: %s, %s', user, old_cmd)
                continue
            elif is_before(old_cmd.time, new_time=new_time):
                self.warning('login command expired: %s, %s', user, old_cmd)
                return False
            elif old_cmd.to_dict() == content.to_dict():
                self.warning('same command, no need to update: %s, terminal=%s', user, terminal)
                return True
            # old record found, update it
            self.info('update login command: %d/%d, %s, terminal=%s', index, len(records), user, terminal)
            records[index] = (content, msg)
            updated = True
            # break
        if not updated:
            # same terminal not found
            self.info('insert new login command: %s, terminal=%s', user, terminal)
            item = (content, msg)
            records.append(item)
        #
        #  build task for saving
        #
        task = self._new_task(user=naked)
        return await task.save(value=records)

    # Override
    async def get_login_command_messages(self, user: ID) -> List[Tuple[LoginCommand, ReliableMessage]]:
        naked = naked_id(did=user)
        return await self._load_login_command_messages(user=naked)
