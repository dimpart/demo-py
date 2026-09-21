# -*- coding: utf-8 -*-
#
#   DIM-SDK : Decentralized Instant Messaging Software Development Kit
#
#                                Written in 2019 by Moky <albert.moky@gmail.com>
#
# ==============================================================================
# MIT License
#
# Copyright (c) 2019 Albert Moky
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
from typing import Iterable

from dimsdk import ID, Meta, Document
from dimsdk import ReliableMessage
from dimsdk import Envelope, Content
from dimsdk import BaseCommandProcessor
from dimsdk import shared_account_extensions

from dimax import MetaCommand, DocumentCommand

from ..archivist import CommonArchivist


class MetaCommandProcessor(BaseCommandProcessor):

    @property  # protected
    def archivist(self) -> Optional[CommonArchivist]:
        facebook = self.facebook
        if facebook is not None:
            return facebook.barrack

    # Override
    async def process_content(self, content: Content, r_msg: ReliableMessage) -> List[Content]:
        assert isinstance(content, MetaCommand), f'meta command error: {content}'
        identifier = content.identifier
        meta = content.meta
        if identifier is None:
            # assert False, f'meta ID cannot empty: {content}'
            text = 'Meta command error.'
            return self._respond_receipt(text=text, content=content, envelope=r_msg.envelope)
        elif meta is None:
            # query meta for ID
            return await self._get_meta(identifier=identifier, content=content, envelope=r_msg.envelope)
        else:
            # received a meta for ID
            return await self._put_meta(meta=meta, identifier=identifier, content=content, envelope=r_msg.envelope)

    # private
    async def _get_meta(self, identifier: ID, content: MetaCommand, envelope: Envelope) -> List[Content]:
        meta = await self.facebook.get_meta(identifier=identifier)
        if meta is None:
            text = 'Meta not found.'
            return self._respond_receipt(text=text, content=content, envelope=envelope, extra={
                'template': 'Meta not found: ${did}.',
                'replacements': {
                    'did': str(identifier),
                }
            })
        # meta got
        return await self._respond_meta(meta=meta, identifier=identifier, receiver=envelope.sender)

    # noinspection PyMethodMayBeStatic
    async def _respond_meta(self, meta: Meta, identifier: ID, receiver: ID) -> List[Content]:
        if receiver.is_same_as(other=identifier):
            # assert False, f'cycled response: {identifier}'
            return []
        # TODO: check response expired
        return [
            MetaCommand.response(identifier=identifier, meta=meta)
        ]

    # private
    async def _put_meta(self, meta: Meta, identifier: ID, content: MetaCommand, envelope: Envelope) -> List[Content]:
        # 1. try to save meta
        errors = await self._save_meta(identifier=identifier, meta=meta, content=content, envelope=envelope)
        if errors is not None:
            # failed
            return errors
        # 2. success
        text = 'Meta received.'
        return self._respond_receipt(text=text, content=content, envelope=envelope, extra={
            'template': 'Meta received: ${did}.',
            'replacements': {
                'did': str(identifier),
            }
        })

    # protected
    async def _save_meta(self, meta: Meta, identifier: ID,
                         content: MetaCommand, envelope: Envelope) -> Optional[List[Content]]:
        # check meta
        if not await self._check_meta(meta=meta, identifier=identifier):
            text = 'Meta not valid.'
            return self._respond_receipt(text=text, content=content, envelope=envelope, extra={
                'template': 'Meta not valid: ${did}.',
                'replacements': {
                    'did': str(identifier),
                }
            })
        elif not await self.archivist.save_meta(meta=meta, identifier=identifier):
            text = 'Meta not accepted.'
            return self._respond_receipt(text=text, content=content, envelope=envelope, extra={
                'template': 'Meta not accepted: ${did}.',
                'replacements': {
                    'did': str(identifier),
                }
            })
        # meta saved, return no error

    # noinspection PyMethodMayBeStatic
    async def _check_meta(self, meta: Meta, identifier: ID) -> bool:
        if not meta.is_valid:
            return False
        old = identifier.address
        gen = meta.generate_id(network=old.network)
        return old == gen.address


class DocumentCommandProcessor(MetaCommandProcessor):

    # Override
    async def process_content(self, content: Content, r_msg: ReliableMessage) -> List[Content]:
        assert isinstance(content, DocumentCommand), f'document command error: {content}'
        identifier = content.identifier
        documents = content.documents
        if identifier is None:
            # assert False, f'doc ID cannot be empty: {content}'
            text = 'Document command error.'
            return self._respond_receipt(text=text, content=content, envelope=r_msg.envelope)
        elif documents is None:
            # query entity document for ID
            return await self._get_documents(identifier=identifier, content=content, envelope=r_msg.envelope)
        else:
            # received new documents
            return await self._put_docs(documents, identifier=identifier, content=content, envelope=r_msg.envelope)

    # private
    async def _get_documents(self, identifier: ID, content: DocumentCommand, envelope: Envelope) -> List[Content]:
        facebook = self.facebook
        documents = await facebook.get_documents(identifier=identifier)
        if documents is None or len(documents) == 0:
            text = 'Document not found.'
            return self._respond_receipt(text=text, content=content, envelope=envelope, extra={
                'template': 'Document not found: ${did}.',
                'replacements': {
                    'did': str(identifier),
                }
            })
        # document got
        query_time = content.last_time
        if query_time is not None:
            # check last document time
            last = self._last_document(documents=documents)
            assert last is not None, 'should not happen'
            last_time = None if last is None else last.time
            if last_time is None:
                assert False, f'document error: {last}'
            elif not last_time.after(query_time):
                # document not updated
                text = 'Document not updated.'
                return self._respond_receipt(text=text, content=content, envelope=envelope, extra={
                    'template': 'Document not updated: ${did}, last time: ${time}.',
                    'replacements': {
                        'did': str(identifier),
                        'time': last_time.timestamp,
                    }
                })
        # documents got
        return await self._respond_documents(documents=documents, identifier=identifier, receiver=envelope.sender)

    # protected
    async def _respond_documents(self, documents: List[Document], identifier: ID, receiver: ID) -> List[Content]:
        # if receiver.is_same_as(other=identifier):
        if receiver == identifier:
            # assert False, f'cycled response: {identifier}'
            return []
        # TODO: check response expired
        meta = await self.facebook.get_meta(identifier=identifier)
        return [
            DocumentCommand.response(identifier=identifier, meta=meta, documents=documents)
        ]

    # noinspection PyMethodMayBeStatic
    def _last_document(self, documents: Iterable[Document]) -> Optional[Document]:
        last_doc = None
        last_time = None
        for doc in documents:
            doc_time = doc.time
            if last_doc is None:
                # first document
                last_doc = doc
                last_time = doc_time
            elif last_time is None:
                # the first document has no time (old version),
                # if this document has time, use the new one
                if doc_time is not None:
                    # first document with time
                    last_doc = doc
                    last_time = doc_time
            elif doc_time is not None and doc_time.after(last_time):
                # new document
                last_doc = doc
                last_time = doc_time
        # OK
        return last_doc

    # private
    async def _put_docs(self, documents: List[Document], identifier: ID,
                        content: DocumentCommand, envelope: Envelope) -> List[Content]:
        facebook = self.facebook
        meta = content.meta
        # 0. check meta
        if meta is None:
            meta = await facebook.get_meta(identifier=identifier)
            if meta is None:
                text = 'Meta not found.'
                return self._respond_receipt(text=text, content=content, envelope=envelope, extra={
                    'template': 'Meta not found: ${did}.',
                    'replacements': {
                        'did': str(identifier),
                    }
                })
        else:
            # 1. try to save meta
            errors = await self._save_meta(meta=meta, identifier=identifier, content=content, envelope=envelope)
            if errors is not None:
                # failed
                return errors
        # 2. try to save documents
        errors = []
        for doc in documents:
            array = await self._save_document(doc, meta=meta, identifier=identifier, content=content, envelope=envelope)
            if isinstance(array, list):
                # failed
                errors.extend(array)
        if len(errors) > 0:
            # failed
            return errors
        # 3. success
        text = 'Document received.'
        return self._respond_receipt(text=text, content=content, envelope=envelope, extra={
            'template': 'Document received: ${did}.',
            'replacements': {
                'did': str(identifier),
            }
        })

    # protected
    async def _save_document(self, doc: Document, meta: Meta, identifier: ID,
                             content: DocumentCommand, envelope: Envelope) -> Optional[List[Content]]:
        # check document
        if not await self._check_document(doc, meta=meta, identifier=identifier):
            # document invalid
            text = 'Document not accepted.'
            return self._respond_receipt(text=text, content=content, envelope=envelope, extra={
                'template': 'Document not accepted: ${did}.',
                'replacements': {
                    'did': str(identifier),
                }
            })
        elif not await self.archivist.save_document(document=doc, identifier=identifier):
            # document expired
            text = 'Document not changed.'
            return self._respond_receipt(text=text, content=content, envelope=envelope, extra={
                'template': 'Document not changed: ${did}.',
                'replacements': {
                    'did': str(identifier),
                }
            })
        # document saved, return no error

    # protected
    async def _check_document(self, doc: Document, meta: Meta, identifier: ID) -> bool:
        # check meta with ID
        ok = await self._check_meta(meta=meta, identifier=identifier)
        if not ok:
            # meta error
            return False
        # check document ID
        helper = shared_account_extensions.handler
        info = doc.to_map()
        did = helper.get_document_id(document=info)
        if did is None:
            assert False, f'document ID not found: {doc}'
        elif not did.is_same_as(other=identifier):
            # assert False, f'ID not matched: {identifier}, {doc}'
            return False
        # NOTICE: if this is a bulletin document for group,
        #             verify it with the group owner's meta.key
        #         else (this is a visa document for user)
        #             verify it with the user's meta.key
        meta_key = meta.public_key
        return doc.verify(public_key=meta_key)
        # TODO: check for group document
