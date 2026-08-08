# -*- coding: utf-8 -*-
#
#   DIM-SDK : Decentralized Instant Messaging Software Development Kit
#
#                                Written in 2024 by Moky <albert.moky@gmail.com>
#
# ==============================================================================
# MIT License
#
# Copyright (c) 2024 Albert Moky
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

from typing import Optional, Union, List
from typing import Iterable

from dimsdk import final

from dimsdk import utf8_encode
from dimsdk import Converter
from dimsdk import DateTime
from dimsdk import TransportableData

from dimsdk import VerifyKey

from dimsdk import Address, ID, Meta
from dimsdk import Document, Visa, Bulletin

from dimplugins.mem.ext import account_helper

from ...utils import list_remove_where
from ...utils import Log
from ...utils import StrMap, MutableStrMap


@final
class IDUtils:

    @classmethod
    def contains(cls, did: ID, members: List[ID]) -> bool:
        for item in members:
            if did.is_same_as(other=item):
                return True
        return False


@final
class MetaUtils:

    @classmethod
    def get_meta_type(cls, meta: StrMap) -> Optional[str]:
        if isinstance(meta, Meta):
            meta = meta.to_map()
        helper = account_helper()
        return helper.get_meta_type(meta=meta)

    @classmethod
    def match_id(cls, identifier: ID, meta: Meta) -> bool:
        assert meta.is_valid, f'meta not valid: {meta}'
        # check ID.name
        seed = meta.seed
        name = identifier.name
        if name is None or len(name) == 0:
            if seed is not None and len(seed) > 0:
                return False
        elif name != seed:
            return False
        # check ID.address
        old = identifier.address
        gen = Address.generate(meta, old.network)
        return old == gen

    @classmethod
    def match_public_key(cls, key: VerifyKey, meta: Meta) -> bool:
        assert meta.is_valid, f'meta not valid: {meta}'
        # check whether the public key equals to meta.key
        if key == meta.public_key:
            return True
        # check with seed & fingerprint
        seed = meta.seed
        if seed is None or len(seed) == 0:
            # NOTICE: ID with BTC/ETH address has no username, so
            #         just compare the key.data to check matching
            return False
        ted = meta.fingerprint
        fingerprint = None if ted is None else ted.to_bytes()
        if fingerprint is None or len(fingerprint) == 0:
            # fingerprint should not be empty here
            return False
        # check whether keys equal by verifying signature
        data = utf8_encode(string=seed)
        return key.verify(data=data, signature=fingerprint)


@final
class DocumentUtils:

    @classmethod
    def get_document_type(cls, document: StrMap) -> Optional[str]:
        if isinstance(document, Document):
            document = document.to_map()
        helper = account_helper()
        return helper.get_document_type(document=document)

    @classmethod
    def get_document_id(cls, document: StrMap) -> Optional[ID]:
        if isinstance(document, Document):
            document = document.to_map()
        helper = account_helper()
        return helper.get_document_id(document=document)

    @classmethod
    def get_visa_terminal(cls, document: Visa) -> Optional[str]:
        terminal = document.get_str(key='terminal')
        if terminal is None or terminal == '':
            did = cls.get_document_id(document=document)
            if did is None:
                return None
            terminal = did.terminal
            if terminal is None or terminal == '':
                # '*'
                return None
        # OK
        return terminal

    @classmethod
    def get_document_name(cls, document: Document) -> Optional[str]:
        value = document.get_property(name='name')
        return Converter.get_str(value=value)

    @classmethod
    def is_before(cls, old_time: Optional[DateTime], this_time: Optional[DateTime]) -> bool:
        """ Check whether this time is before old time """
        if old_time is None or this_time is None:
            return False
        else:
            return this_time.before(old_time)

    @classmethod
    def is_expired(cls, this_doc: Document, old_doc: Document) -> bool:
        """ Check whether this document's time is before old document's time """
        return cls.is_before(old_time=old_doc.time, this_time=this_doc.time)

    @classmethod
    def last_document(cls, documents: Iterable[Document], doc_type: str = '*') -> Optional[Document]:
        """ Select last document matched the type """
        if documents is None:
            return None
        elif doc_type is None or doc_type == '*':
            doc_type = ''
        check_type = len(doc_type) > 0
        last: Optional[Document] = None
        for item in documents:
            # 1. check type
            if check_type:
                item_type = cls.get_document_type(document=item)
                if item_type is not None and len(item_type) > 0 and item_type != doc_type:
                    # type not matched, skip it
                    continue
            # 2. check time
            if last is not None and cls.is_expired(this_doc=item, old_doc=last):
                # skip expired document
                continue
            # got it
            last = item
        return last

    @classmethod
    def last_visa(cls, documents: Iterable[Document], terminal: str = '*') -> Optional[Visa]:
        """ Select last visa document """
        if documents is None:
            return None
        last: Optional[Visa] = None
        for item in documents:
            # 1. check type
            if not isinstance(item, Visa):
                # type not matched, skip it
                continue
            # 2. check terminal
            if terminal != '*' and terminal != cls.get_visa_terminal(document=item):
                # terminal not matched, skip it
                continue
            # 3. check time
            if last is not None and cls.is_expired(this_doc=item, old_doc=last):
                # skip expired document
                continue
            # got it
            last = item
        return last

    @classmethod
    def last_bulletin(cls, documents: Iterable[Document]) -> Optional[Bulletin]:
        """ Select last bulletin document """
        if documents is None:
            return None
        last: Optional[Bulletin] = None
        for item in documents:
            # 1. check type
            if not isinstance(item, Bulletin):
                # type not matched, skip it
                continue
            # 2. check time
            if last is not None and cls.is_expired(this_doc=item, old_doc=last):
                # skip expired document
                continue
            # got it
            last = item
        return last

    @classmethod
    def sort_documents(cls, documents: List[Document]) -> List[Document]:
        """ Sort documents by timestamp descending """
        documents.sort(
            # key=lambda x: -(x.time or 0.0)
            key=lambda x: 0.0 if x.time is None else -x.time
        )
        return documents

    @classmethod
    def tidy_documents(cls, documents: List[Document]) -> List[Document]:
        """ Remove duplicated items by signature """
        signatures = set()

        def should_remove(doc: Document) -> bool:
            did = cls.get_document_id(document=doc)
            sig = doc.get_str(key='signature')
            if sig is None or sig in signatures:
                assert sig is not None, f'document info error: {did}, {doc}'
                Log.warning('skip duplicated document: %s, %s', did, doc)
                return True
            else:
                signatures.add(sig)
            # TODO: remove expired document(s)
            return False

        list_remove_where(documents, predicate=should_remove)
        return documents

    #
    #   Local Storage
    #

    @classmethod
    def dump_documents(cls, documents: List[Document]) -> StrMap:
        """ Serialize documents """
        # sort and remove duplicated item
        Log.info('Dump %d document(s)', len(documents))
        array = Document.revert(documents=documents)
        return {
            'documents': array,
        }

    @classmethod
    def pump_documents(cls, info: Union[StrMap, List]) -> Optional[List[Document]]:
        """ Deserialize documents """
        array = _fetch_documents(info=info)
        if array is None:
            return None
        # convert documents
        documents = []
        for item in array:
            doc = cls._create_document(info=item)
            if doc is not None:
                documents.append(doc)
            else:
                Log.error('document error: %s', item)
        # done
        Log.info('Pump %d document(s)', len(documents))
        return documents

    @classmethod
    def _create_document(cls, info: MutableStrMap) -> Optional[Document]:
        """ Local creation  """
        _fix_did(content=info)
        # 0. check document id
        did = cls.get_document_id(document=info)
        if did is None:
            Log.error('document id error: %s', info)
            # return None
        # 1. check document type
        doc_type = cls.get_document_type(document=info)
        if doc_type is None:
            doc_type = '*'
        # 2. check document data & signature
        data = info.get('data')
        if data is None:
            # compatible with v1.0
            data = info.get('profile')
        signature = info.get('signature')
        ted = TransportableData.parse(signature)
        if data is None or len(data) == 0 or ted is None or ted.is_empty:
            Log.error('document data error: %s', info)
            return None
        # 3. create document with data + signature from local storage
        doc = Document.create(doc_type=doc_type, data=data, signature=ted)
        for key, value in info.items():
            if key == 'data' or key == 'signature':
                continue
            elif key == 'ID':
                continue
            doc[key] = value
        return doc


def _fix_did(content: MutableStrMap):
    did = content.get('did')
    if did is None:
        # 'did' not exists, copy the value from 'ID'
        did = content.get('ID')
        if did is not None:
            content['did'] = did
        # else:
        #     assert False, f'did not exists: {content}'
    elif 'ID' in content:
        # these two values must be equal
        assert content.get('ID') == did, f'did error: {content}'
    else:
        # copy value from 'did' to 'ID'
        content['ID'] = did


def _fetch_documents(info: Union[StrMap, List]) -> Optional[List]:
    if isinstance(info, list):
        return info
    elif isinstance(info, dict):
        docs = info.get('documents')
        if isinstance(docs, list):
            return docs
        elif 'data' in info and 'signature' in info:
            return [info]
    # error
    Log.error('documents error: %s', info)
    return None
