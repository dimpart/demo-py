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

from typing import Optional, List

from dimsdk import ID

from ...utils import template_replace

from .base import Storage


class GroupStorage(Storage):
    """
        Group Storage
        ~~~~~~~~~~~~~

        file path: '.dim/protected/{ADDRESS}/members.js'
        file path: '.dim/protected/{ADDRESS}/administrators.js'
    """

    members_path = '{PROTECTED}/{ADDRESS}/members.js'
    administrators_path = '{PROTECTED}/{ADDRESS}/administrators.js'

    def show_info(self):
        path1 = self.protected_path(self.members_path)
        path2 = self.protected_path(self.administrators_path)
        print('!!!        members path: %s' % path1)
        print('!!! administrators path: %s' % path2)

    def __members_path(self, identifier: ID) -> str:
        path = self.protected_path(self.members_path)
        address = str(identifier.address)
        return template_replace(path, key='ADDRESS', value=address)

    def __administrators_path(self, identifier: ID) -> str:
        path = self.protected_path(self.administrators_path)
        address = str(identifier.address)
        return template_replace(path, key='ADDRESS', value=address)

    # async def get_founder(self, group: ID) -> Optional[ID]:
    #     pass
    #
    # async def get_owner(self, group: ID) -> Optional[ID]:
    #     pass

    async def load_members(self, group: ID) -> Optional[List[ID]]:
        """ load members from file """
        path = self.__members_path(identifier=group)
        self.info('Loading members from: %s', path)
        users = await self.read_json(path=path)
        if isinstance(users, list):
            return ID.convert(array=users)

    async def save_members(self, members: List[ID], group: ID) -> bool:
        """ save members into file """
        path = self.__members_path(identifier=group)
        self.info('Saving members into: %s', path)
        return await self.write_json(container=ID.revert(identifiers=members), path=path)

    async def load_administrators(self, group: ID) -> Optional[List[ID]]:
        """ load administrators from file """
        path = self.__administrators_path(identifier=group)
        self.info('Loading administrators from: %s', path)
        users = await self.read_json(path=path)
        if isinstance(users, list):
            return ID.convert(array=users)

    async def save_administrators(self, administrators: List[ID], group: ID) -> bool:
        """ save administrators into file """
        path = self.__administrators_path(identifier=group)
        self.info('Saving administrators into: %s', path)
        return await self.write_json(container=ID.revert(identifiers=administrators), path=path)
