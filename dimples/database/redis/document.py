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

from typing import Optional, List

from dimsdk import ID, Document

from ...utils import utf8_encode, utf8_decode, json_encode, json_decode
from ...common import DocumentUtils

from .base import RedisCache


class DocumentCache(RedisCache):

    # document cached in Redis will be removed after 30 minutes, after that
    # it will be reloaded from local storage if it's still need.
    EXPIRES = 1800  # seconds

    @property  # Override
    def db_name(self) -> Optional[str]:
        return 'mkm'

    @property  # Override
    def tbl_name(self) -> str:
        return 'document'

    """
        Document for Entities (User/Group)
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        redis key: 'mkm.documents.{ADDRESS}'
    """
    def __cache_name(self, identifier: ID) -> str:
        address = str(identifier.address)
        return '%s.%s.%s' % (self.db_name, self.tbl_name, address)

    async def save_documents(self, documents: List[Document], identifier: ID) -> bool:
        """ cache documents """
        info = DocumentUtils.dump_documents(documents=documents)
        js = json_encode(container=info)
        value = utf8_encode(string=js)
        name = self.__cache_name(identifier=identifier)
        # self.info('Caching %d document(s) for key: %s', len(documents), name)
        return await self.set(name=name, value=value, expires=self.EXPIRES)

    async def load_documents(self, identifier: ID) -> Optional[List[Document]]:
        """ load documents from cache """
        name = self.__cache_name(identifier=identifier)
        value = await self.get(name=name)
        if value is None:
            # not found
            return None
        js = utf8_decode(data=value)
        assert js is not None, f'failed to decode string: {value}'
        info = json_decode(string=js)
        # load documents from cache server
        return DocumentUtils.pump_documents(info=info)
