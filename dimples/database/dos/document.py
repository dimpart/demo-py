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

from dimsdk import ID, Document

from ...utils import template_replace
from ...common import DocumentUtils

from .base import Storage


class DocumentStorage(Storage):
    """
        Document for Entities (User/Group)
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        file path: '.dim/public/{ADDRESS}/documents.js'
    """
    docs_path = '{PUBLIC}/{ADDRESS}/documents.js'

    def show_info(self):
        path = self.public_path(self.docs_path)
        print('!!!      documents path: %s' % path)

    def __docs_path(self, identifier: ID) -> str:
        path = self.public_path(self.docs_path)
        address = str(identifier.address)
        return template_replace(path, key='ADDRESS', value=address)

    async def save_documents(self, documents: List[Document], identifier: ID) -> bool:
        """ save documents into file """
        info = DocumentUtils.dump_documents(documents=documents)
        path = self.__docs_path(identifier=identifier)
        self.info('Saving %d document(s) into: %s', len(documents), path)
        return await self.write_json(container=info, path=path)

    async def load_documents(self, identifier: ID) -> Optional[List[Document]]:
        """ load documents from file """
        path = self.__docs_path(identifier=identifier)
        # self.info('Loading documents from: %s', path)
        info = await self.read_json(path=path)
        if info is None:
            # file not found
            self.warning('document file not found: %s', path)
            return None
        # load documents from local storage
        documents = DocumentUtils.pump_documents(info=info)
        if documents is None:
            self.error('documents error: %s -> %s', identifier, path)
        else:
            self.info('Loaded %d document(s) from: %s', len(documents), path)
        return documents
