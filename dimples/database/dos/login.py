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

from typing import Tuple, List, Dict

from dimsdk import ID
from dimsdk import ReliableMessage
from dimsdk import Command

from ...utils import template_replace
from ...common import LoginCommand

from .base import Storage


class LoginStorage(Storage):
    """
        Login Command Storage
        ~~~~~~~~~~~~~~~~~~~~~
        file path: '.dim/public/{ADDRESS}/login_commands.js'
    """

    login_path = '{PUBLIC}/{ADDRESS}/login_commands.js'

    def show_info(self):
        path = self.public_path(self.login_path)
        print(f'!!!      login cmd path: {path}')

    def __login_path(self, identifier: ID) -> str:
        path = self.public_path(self.login_path)
        return template_replace(path, key='ADDRESS', value=str(identifier.address))

    async def load_login_command_messages(self, user: ID) -> List[Tuple[LoginCommand, ReliableMessage]]:
        """ load login commands from file """
        path = self.__login_path(identifier=user)
        self.info('Loading login commands from: %s', path)
        info = await self.read_json(path=path)
        if info is None:
            self.warning('failed to load "login" commands: %s from %s', user, path)
            return []
        assert isinstance(info, Dict), f'login records error: {user} => {info}'
        array = info.get('records')
        if array is None:
            self.error('login records error: %s => %s', user, info)
            return []
        # OK
        return parse_login_records(array=array)

    async def save_login_command_messages(self, records: List[Tuple[LoginCommand, ReliableMessage]], user: ID) -> bool:
        """ save login commands into file """
        array = []
        for cmd, msg in records:
            array.append({
                'cmd': cmd.to_dict(),
                'msg': msg.to_dict(),
            })
        info = {
            'records': array,
        }
        path = self.__login_path(identifier=user)
        self.info('Saving login command into: %s', path)
        return await self.write_json(container=info, path=path)


def parse_login_records(array: List) -> List[Tuple[LoginCommand, ReliableMessage]]:
    records = []
    for item in array:
        cmd = item.get('cmd')
        msg = item.get('msg')
        cmd = Command.parse(content=cmd)
        msg = ReliableMessage.parse(msg=msg)
        if cmd is None or msg is None:
            continue
        assert isinstance(cmd, LoginCommand), f'login command error: {cmd}'
        rec = (cmd, msg)
        records.append(rec)
    # OK
    return records
