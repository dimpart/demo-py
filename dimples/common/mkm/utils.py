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

from typing import Optional, Union, Iterable, List, Dict

from dimsdk import utf8_encode
from dimsdk import Converter
from dimsdk import DateTime
from dimsdk import TransportableData

from dimsdk import VerifyKey

from dimsdk import Address, ID, Meta
from dimsdk import Document, Visa, Bulletin

from dimplugins.mem.ext import account_helper

from ...utils import Log


class MetaUtils:

    @classmethod
    def get_meta_type(cls, meta: Union[Dict, Meta]) -> Optional[str]:
        if isinstance(meta, Meta):
            meta = meta.to_dict()
        helper = account_helper()
        return helper.get_meta_type(meta=meta)

    @classmethod
    def match_id(cls, identifier: ID, meta: Meta) -> bool:
        assert meta.is_valid, 'meta not valid: %s' % meta
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
        assert meta.is_valid, 'meta not valid: %s' % meta
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


class DocumentUtils:

    @classmethod
    def get_document_type(cls, document: Union[Dict, Document]) -> Optional[str]:
        if isinstance(document, Document):
            document = document.to_dict()
        helper = account_helper()
        return helper.get_document_type(document=document)

    @classmethod
    def get_document_id(cls, document: Union[Dict, Document]) -> Optional[ID]:
        if isinstance(document, Document):
            document = document.to_dict()
        helper = account_helper()
        return helper.get_document_id(document=document)

    @classmethod
    def get_terminal(cls, document: Document) -> Optional[str]:
        terminal = document.get_str(key='terminal')
        if terminal is not None and len(terminal) > 0:
            return terminal
        did = cls.get_document_id(document=document)
        if did is not None:
            terminal = did.terminal
            if terminal is not None and len(terminal) > 0:
                return terminal
        # '*'
        return None

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
    def last_document(cls, documents: Iterable[Document], doc_type: str = None) -> Optional[Document]:
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
    def last_visa(cls, documents: Iterable[Document]) -> Optional[Visa]:
        """ Select last visa document """
        if documents is None:
            return None
        last: Optional[Visa] = None
        for item in documents:
            # 1. check type
            if not isinstance(item, Visa):
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

    #
    #   Local Storage
    #

    @classmethod
    def dump_documents(cls, documents: List[Document]) -> Dict:
        """ Serialize documents """
        # sort and remove duplicated item
        docs = _sort_documents(documents=documents)
        Log.info('Dump %d/%d document(s)', len(docs), len(documents))
        return {
            'documents': [d.to_dict() for d in docs],
        }

    @classmethod
    def pump_documents(cls, info: Union[Dict, List]) -> Optional[List[Document]]:
        """ Deserialize documents """
        array = _fetch_documents(info=info)
        if array is not None:
            documents = []
            # convert documents
            for item in array:
                doc = cls._create_document(info=item)
                if doc is not None:
                    documents.append(doc)
                else:
                    Log.error('document error: %s', item)
            # sort and remove duplicated item
            docs = _sort_documents(documents=documents)
            Log.info('Pump %d/%d document(s)', len(docs), len(array))
            return documents

    @classmethod
    def _create_document(cls, info: Dict) -> Optional[Document]:
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


def _fix_did(content: Dict):
    did = content.get('did')
    if did is None:
        # 'did' not exists, copy the value from 'ID'
        did = content.get('ID')
        if did is not None:
            content['did'] = did
        # else:
        #     assert False, 'did not exists: %s' % content
    elif 'ID' in content:
        # these two values must be equal
        assert content.get('ID') == did, 'did error: %s' % content
    else:
        # copy value from 'did' to 'ID'
        content['ID'] = did


def _fetch_documents(info: Union[Dict, List]) -> Optional[List]:
    if isinstance(info, List):
        return info
    elif isinstance(info, Dict):
        docs = info.get('documents')
        if isinstance(docs, List):
            return docs
        elif 'data' in info and 'signature' in info:
            return [info]
    # error
    Log.error('documents error: %s', info)
    return None


def _sort_documents(documents: List[Document]) -> List[Document]:
    # 1. sort by time DESC
    sorted_docs = sorted(
        documents,
        # key=lambda x: -(x.time or 0.0)
        key=lambda x: 0.0 if x.time is None else -float(x.time)
    )
    # 2. remove duplicated item
    signatures = set()
    array = []
    for doc in sorted_docs:
        # check signature
        sig = doc.get('signature')
        if sig is None or sig in signatures:
            Log.warning('skip duplicated document: %s, %s', sig, doc)
            continue
        else:
            signatures.add(sig)
        # next document
        array.append(doc)
    # done
    return array
