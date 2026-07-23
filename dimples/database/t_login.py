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
from ..utils import is_before
from ..common import CommandMessageUtils
from ..common import LoginDBI, LoginCommand

from .dos import LoginStorage
from .redis import LoginCache

from .t_base import DbTask, DataCache


class CmdTask(DbTask[ID, List[Tuple[LoginCommand, ReliableMessage]]]):

    def __init__(self, user: ID,
                 new_cmd: Optional[LoginCommand],
                 new_msg: Optional[ReliableMessage],
                 redis: LoginCache, storage: LoginStorage,
                 mutex_lock: threading.Lock, cache_pool: CachePool):
        super().__init__(mutex_lock=mutex_lock, cache_pool=cache_pool)
        self._user = user
        self._new_cmd = new_cmd
        self._new_msg = new_msg
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
        if array is not None:
            CommandMessageUtils.sort_commands(records=array)
            return array
        # 3. the local storage will return a tuple with None values, when command not found
        array = await self._dos.load_login_command_messages(user=self._user)
        if array is not None:
            CommandMessageUtils.sort_commands(records=array)
        else:
            # 4. return a tuple with None values as a placeholder for the memory cache
            array = []
        # 5. update redis server
        await self._redis.save_login_command_messages(records=array, user=self._user)
        return array

    # Override
    async def _write_data(self, records: List[Tuple[LoginCommand, ReliableMessage]]) -> bool:
        new_cmd = self._new_cmd
        new_msg = self._new_msg
        if new_cmd is None or new_msg is None:
            assert False, 'should not happen: %s' % self._user
        else:
            new_sn = new_cmd.sn
            new_time = new_cmd.time
            identifier = new_cmd.identifier
            terminal = CommandMessageUtils.get_login_terminal(content=new_cmd)
        # check did
        if not identifier.is_same_as(other=self._user):
            self.error('login id not matched: %s, %s', identifier, self._user)
            return False
        #
        #   0. check old records
        #
        updated = False
        index = len(records)
        while index > 0:
            index -= 1
            cmd, msg = records[index]
            assert isinstance(cmd, LoginCommand), f'login command error: {cmd}'
            # check login id
            did = cmd.identifier
            if not did.is_same_as(other=identifier):
                self.error('login command not matched: %s => %s', identifier, cmd)
                # TODO: remove it?
                continue
            elif cmd.sn == new_sn:
                self.warning('same login command, no need to update:: %s, "%s"', identifier, terminal)
                return True
            elif CommandMessageUtils.get_login_terminal(content=cmd) != terminal:
                self.info('skip login record: %s, "%s", %s', identifier, terminal, cmd)
                continue
            elif is_before(cmd.time, new_time=new_time):
                self.warning('login command expired: %s, "%s", %s', identifier, terminal, cmd)
                return False
            # old record found, update it
            self.info('update login: %d/%d, %s, "%s"', index, len(records), identifier, terminal)
            records[index] = (new_cmd, new_msg)
            updated = True
            # break
        if not updated:
            # same terminal not found
            self.info('insert login record: %s, "%s"', identifier, terminal)
            rec = (new_cmd, new_msg)
            records.append(rec)
        # sort after changed
        CommandMessageUtils.sort_commands(records=records)
        #
        #   1. store into redis server
        #
        ok1 = await self._redis.save_login_command_messages(records=records, user=self._user)
        #
        #   2. save into local storage
        #
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

    def _new_task(self, user: ID, new_cmd: LoginCommand = None, new_msg: ReliableMessage = None) -> CmdTask:
        terminal = user.terminal
        if terminal is not None:
            if new_cmd is not None:
                old = new_cmd.get('terminal')
                if old is None or old == '':
                    new_cmd['terminal'] = terminal
            # Naked ID
            user = user.without_terminal()
        # create task with naked id
        return CmdTask(user=user, new_cmd=new_cmd, new_msg=new_msg,
                       redis=self._redis, storage=self._dos,
                       mutex_lock=self._mutex_lock, cache_pool=self._cache_pool)

    #
    #   Login DBI
    #

    # Override
    async def save_login_command_message(self, user: ID, content: LoginCommand, msg: ReliableMessage) -> bool:
        #
        #  0. check valid
        #
        did = content.identifier
        if not user.is_same_as(other=did):
            self.error('login id not matched: %s, %s', did, user)
            return False
        #
        #  1. load old records
        #
        task = self._new_task(user=user)
        array = await task.load()
        if array is None:
            array = []
        #
        #   2. save new record
        #
        task = self._new_task(user=user, new_cmd=content, new_msg=msg)
        return await task.save(array)

    # Override
    async def get_login_command_messages(self, user: ID) -> List[Tuple[LoginCommand, ReliableMessage]]:
        #
        #  build task for loading
        #
        task = self._new_task(user=user)
        array = await task.load()
        return [] if array is None else array
