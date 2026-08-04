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

from typing import Optional, List

from dimsdk import final

from dimsdk import ID, ANYONE, FOUNDER

from dimsdk import Meta, Visa, Document
from dimsdk import Message


@final
class BroadcastUtils:

    @classmethod  # private
    def group_seed(cls, group: ID) -> Optional[str]:
        name = group.name
        if name is not None:
            length = len(name)
            if length > 0 and (length != 8 or name.lower() != 'everyone'):
                return name

    @classmethod  # protected
    def broadcast_founder(cls, group: ID) -> Optional[ID]:
        name = cls.group_seed(group=group)
        if name is None:
            # Consensus: the founder of group 'everyone@everywhere'
            #            'Albert Moky'
            return FOUNDER
        else:
            # DISCUSS: who should be the founder of group 'xxx@everywhere'?
            #          'anyone@anywhere', or 'xxx.founder@anywhere'
            return ID.parse(identifier=name + '.founder@anywhere')

    @classmethod  # protected
    def broadcast_owner(cls, group: ID) -> Optional[ID]:
        name = cls.group_seed(group=group)
        if name is None:
            # Consensus: the owner of group 'everyone@everywhere'
            #            'anyone@anywhere'
            return ANYONE
        else:
            # DISCUSS: who should be the owner of group 'xxx@everywhere'?
            #          'anyone@anywhere', or 'xxx.owner@anywhere'
            return ID.parse(identifier=name + '.owner@anywhere')

    @classmethod  # protected
    def broadcast_members(cls, group: ID) -> List[ID]:
        name = cls.group_seed(group=group)
        if name is None:
            # Consensus: the member of group 'everyone@everywhere'
            #            'anyone@anywhere'
            return [ANYONE]
        else:
            # DISCUSS: who should be the member of group 'xxx@everywhere'?
            #          'anyone@anywhere', or 'xxx.member@anywhere'
            owner = ID.parse(identifier=name + '.owner@anywhere')
            member = ID.parse(identifier=name + '.member@anywhere')
            return [owner, member]


@final
class MessageUtils:

    """
        Sender's Meta
        ~~~~~~~~~~~~~
        Extends for the first message package of 'Handshake' protocol.
    """

    @classmethod
    def get_meta(cls, msg: Message) -> Optional[Meta]:
        meta = msg.get('meta')
        return Meta.parse(meta=meta)

    @classmethod
    def set_meta(cls, meta: Optional[Meta], msg: Message):
        msg.set_map(key='meta', value=meta)

    """
        Sender's Visa
        ~~~~~~~~~~~~~
        Extends for the first message package of 'Handshake' protocol.
    """

    @classmethod
    def get_visa(cls, msg: Message) -> Optional[Visa]:
        visa = msg.get('visa')
        doc = Document.parse(document=visa)
        if isinstance(doc, Visa):
            return doc
        assert doc is None, 'visa document error: %s' % visa

    @classmethod
    def set_visa(cls, visa: Optional[Visa], msg: Message):
        msg.set_map(key='visa', value=visa)

    """
        Message Direction
        ~~~~~~~~~~~~~~~~~
        MAIL FROM: "moky@xxx/abc"
        RCPT TO:   "hulk@yyy/def"
    """

    @classmethod
    def send_from(cls, msg: Message) -> Optional[ID]:
        mail_from = msg.get_str(key='from')
        if mail_from is None:  # or mail_from == '':
            return None
        elif mail_from == '/':
            # Naked ID: "{name}@{address}"
            return msg.sender.without_terminal()
        elif mail_from.startswith('/'):
            # Terminal only: "/{terminal}"
            terminal = mail_from[1:]
            return msg.sender.with_terminal(terminal=terminal)
        else:
            # Dressed ID: "{name}@{address}/{terminal}"
            uid = ID.parse(identifier=mail_from)
            assert msg.sender.is_same_as(other=uid), f'sender error: {msg.sender}, {mail_from}'
            return uid

    @classmethod
    def rcpt_to(cls, msg: Message) -> Optional[ID]:
        rcpt = msg.get_str(key='rcpt')
        if rcpt is None:  # or rcpt == '':
            return None
        else:
            uid = ID.parse(identifier=rcpt)
            assert uid.is_user, f'receiver error: {msg.receiver}, {rcpt}'
            return uid
