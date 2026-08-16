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
from typing import Optional, List

from aiou.mem import CachePool

from dimsdk import DateTime
from dimsdk import ID
from dimsdk import Document, Visa

from ..utils import Config
from ..utils import Log

from ..common import DocumentUtils
from ..common import DocumentDBI

from .dos import DocumentStorage
from .redis import DocumentCache

from .t_base import DbTask, DataCache


def _get_document_terminal(document: Document) -> str:
    if isinstance(document, Visa):
        terminal = DocumentUtils.get_visa_terminal(document=document)
        if terminal is None or terminal == '*':
            terminal = ''
        return terminal
    # bulletin document has no terminal
    return ''


def _types_not_match(type1: Optional[str], type2: Optional[str]) -> bool:
    if type1 is None:
        type1 = ''
    if type2 is None:
        type2 = ''
    if type1 == '*' or type2 == '*':
        return False
    else:
        return type1 != type2


def _sort_documents(documents: List[Document], identifier: ID) -> List[Document]:
    total = len(documents)
    if total > 1:
        # 1. Sort documents by timestamp descending
        DocumentUtils.sort_documents(documents=documents)
        # 2. Remove duplicated items by signature
        DocumentUtils.tidy_documents(documents=documents)
        # TODO: remove expired document(s)
        if len(documents) > 8:
            del documents[8:]
    count = len(documents)
    if count < total:
        Log.info('trim %d/%d document(s) for %s', count, total, identifier)
    return documents


class DocTask(DbTask[ID, List[Document]]):

    def __init__(self, identifier: ID, new_document: Optional[Document],
                 redis: DocumentCache, storage: DocumentStorage,
                 mutex_lock: threading.Lock, cache_pool: CachePool):
        super().__init__(mutex_lock=mutex_lock, cache_pool=cache_pool)
        self._identifier = identifier
        self._new_doc = new_document
        self._redis = redis
        self._dos = storage

    @property  # Override
    def cache_key(self) -> ID:
        return self._identifier

    # Override
    async def _read_data(self) -> Optional[List[Document]]:
        identifier = self._identifier
        # 1. the redis server will return None when cache not found
        # 2. when redis server return an empty array, no need to check local storage again
        array = await self._redis.load_documents(identifier=identifier)
        if array is not None:
            _sort_documents(documents=array, identifier=identifier)
            return array
        # 3. try to load from local storage
        array = await self._dos.load_documents(identifier=identifier)
        if array is None:
            # 4. create an empty array as a placeholder for the memory cache
            array = []
        else:
            _sort_documents(documents=array, identifier=identifier)
        # 5. update redis server
        await self._redis.save_documents(documents=array, identifier=identifier)
        return array

    # Override
    async def _write_data(self, documents: List[Document]) -> bool:
        entity = self._identifier
        new_doc = self._new_doc
        if new_doc is None:
            assert False, f'should not happen: {entity}'
            # return False
        else:
            new_type = DocumentUtils.get_document_type(document=new_doc)
            new_signature = new_doc.get_str(key='signature', default='')
            new_terminal = _get_document_terminal(document=new_doc)
        # check did
        did = DocumentUtils.get_document_id(document=new_doc)
        if did is None:
            self.warning('document id not found: %s, %s', entity, new_doc)
            # return False
        elif not did.is_same_as(other=entity):
            self.error('document id not matched: %s, %s', entity, new_doc)
            return False
        #
        #   0. check old documents
        #
        updated = False
        total = len(documents)
        index = 0
        for item in documents:
            index += 1
            # check document id
            did = DocumentUtils.get_document_id(document=item)
            if did is None or not did.is_same_as(other=entity):
                self.error('[%d/%d] document id not matched: %s, %s => %s', index, total, entity, did, item)
                # TODO: remove it?
                assert did is None, f'document error: {entity}, {item}'
                # continue
            # check duplicated
            if item.get_str(key='signature') == new_signature:
                self.warning('[%d/%d] document exists: %s, sign=%s.', index, total, did, new_signature)
                return True
            elif item == new_doc:
                self.warning('[%d/%d] same document, no need to update: %s.', index, total, did)
                return True
            # check terminal & type
            device = _get_document_terminal(document=item)
            if device != new_terminal:
                self.info('[%d/%d] skip document: %s, terminal=%s <> %s.', index, total, did, device, new_terminal)
                continue
            ot = DocumentUtils.get_document_type(document=item)
            if _types_not_match(ot, new_type):
                self.info('[%d/%d] skip document: %s, type=%s <> %s.', index, total, did, ot, new_type)
                continue
            # old record found (same type, same terminal),
            # update it
            self.info('[%d/%d] update document: %s, terminal=%s, type=%s', index, total, did, new_terminal, new_type)
            documents[index - 1] = new_doc
            updated = True
            # break
        if not updated:
            # same type + terminal not found
            when = new_doc.get_property(name='created_time')
            when = DateTime.parse(when)
            self.info('insert new document: %s "%s", type="%s", created=[%s].', entity, new_terminal, new_type, when)
            documents.append(new_doc)
        # if document list changed, sort before saving
        _sort_documents(documents=documents, identifier=entity)
        #
        #   1. store into redis server
        #
        ok1 = await self._redis.save_documents(documents=documents, identifier=entity)
        #
        #   2. save into local storage
        #
        ok2 = await self._dos.save_documents(documents=documents, identifier=entity)
        return ok1 or ok2


class DocumentTable(DataCache, DocumentDBI):
    """ Implementations of DocumentDBI """

    def __init__(self, config: Config):
        super().__init__(pool_name='documents')  # ID => List[Document]
        self._redis = DocumentCache(config=config)
        self._dos = DocumentStorage(config=config)

    def show_info(self):
        self._dos.show_info()

    def _new_task(self, identifier: ID, new_document: Document = None) -> DocTask:
        assert identifier.terminal is None, f'not a naked id: {identifier}'
        # create task with naked id
        return DocTask(identifier=identifier, new_document=new_document,
                       redis=self._redis, storage=self._dos,
                       mutex_lock=self._mutex_lock, cache_pool=self._cache_pool)

    #
    #   Document DBI
    #

    # Override
    async def save_document(self, document: Document, identifier: ID) -> bool:
        assert document.is_valid, f'document invalid: {identifier} -> {document}'
        #
        #   1. load old records
        #
        task = self._new_task(identifier=identifier)
        docs = await task.load()
        if docs is None:
            docs = []
        else:
            # check expired
            new_time = document.time
            if new_time is not None:
                for item in docs:
                    old_time = item.time
                    if old_time is not None and old_time > new_time:
                        self.warning('ignore expired document: %s', document)
                        return False
        #
        #   2. save new record
        #
        task = self._new_task(identifier=identifier, new_document=document)
        return await task.save(docs)

    # Override
    async def get_documents(self, identifier: ID) -> List[Document]:
        #
        #  build task for loading
        #
        task = self._new_task(identifier=identifier)
        docs = await task.load()
        return [] if docs is None else docs
