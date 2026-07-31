# -*- coding: utf-8 -*-
# ==============================================================================
# MIT License
#
# Copyright (c) 2023 Albert Moky
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

from dimsdk import EncryptKey
from dimsdk import ID
from dimsdk import InstantMessage, SecureMessage, ReliableMessage
from dimsdk import MessagePacker

from ..utils import StrMap
from ..utils import Logging

from .mkm import DocumentUtils

from .protocol import MessageUtils

from .facebook import CommonFacebook
from .messenger import CommonMessenger

from .queue import SuspendedMessageQueue


class CommonMessagePacker(MessagePacker, Logging):

    def __init__(self, facebook: CommonFacebook, messenger: CommonMessenger):
        super().__init__(facebook=facebook, messenger=messenger)
        self.__queue = SuspendedMessageQueue()

    @property  # Override
    def messenger(self) -> Optional[CommonMessenger]:
        transceiver = super().messenger
        assert isinstance(transceiver, CommonMessenger), f'transceiver error: {transceiver}'
        return transceiver

    def suspend_reliable_message(self, msg: ReliableMessage, error: StrMap):
        self.__queue.suspend_reliable_message(msg=msg, error=error)

    def suspend_instant_message(self, msg: InstantMessage, error: StrMap):
        self.__queue.suspend_instant_message(msg=msg, error=error)

    def resume_reliable_messages(self) -> List[ReliableMessage]:
        return self.__queue.resume_reliable_messages()

    def resume_instant_messages(self) -> List[InstantMessage]:
        return self.__queue.resume_instant_messages()

    #
    #   Checking
    #

    # protected
    async def _visa_key(self, user: ID) -> Optional[EncryptKey]:
        """ for checking whether user's ready """
        db = self.facebook
        # return await db.public_key_for_encryption(identifier=user)
        docs = await db.get_documents(identifier=user)
        if docs is None or len(docs) == 0:
            return None
        visa = DocumentUtils.last_visa(documents=docs)
        if visa is not None:  # and visa.is_valid:
            return visa.public_key
        meta = await db.get_meta(identifier=user)
        if meta is not None:  # and meta.is_valid:
            meta_key = meta.public_key
            if isinstance(meta_key, EncryptKey):
                return meta_key

    async def _check_attachments(self, msg: ReliableMessage) -> bool:
        """ Check meta & visa """
        archivist = self.facebook.archivist
        if archivist is None:
            # assert archivist is not None, 'archivist not ready'
            return False
        else:
            sender = msg.sender
        # [Meta Protocol]
        meta = MessageUtils.get_meta(msg=msg)
        if meta is not None:
            ok = await archivist.save_meta(meta=meta, identifier=sender)
            if not ok:
                self.error('meta error: %s, %s', sender, meta)
                return False
        # [Visa Protocol]
        visa = MessageUtils.get_visa(msg=msg)
        if visa is not None:
            ok = await archivist.save_document(document=visa, identifier=sender)
            if not ok:
                self.error('visa error: %s, %s', sender, visa)
                # FIXME: visa document maybe expired
                # return False
        # OK
        return True

    # protected
    async def _check_sender(self, msg: ReliableMessage) -> bool:
        """ Check sender before verifying received message """
        sender = msg.sender
        assert sender.is_user, f'sender error: {sender}'
        # check sender's meta & visa document
        if await self._visa_key(user=sender) is not None:
            # sender is OK
            return True
        # sender not ready, suspend message for waiting document
        error = {
            'message': 'verify key not found',
            'user': str(sender),
        }
        self.suspend_reliable_message(msg=msg, error=error)  # msg['error'] = error
        return False

    # protected
    async def _check_receiver(self, msg: InstantMessage) -> bool:
        """ Check receiver before encrypting message """
        receiver = msg.receiver
        if receiver.is_broadcast:
            # broadcast message
            return True
        elif receiver.is_group:
            # NOTICE: station will never receive grouped message, so
            #         we don't need to check group info here; and
            #         if a client wants to send group message,
            #         that should be sent to a group bot first,
            #         and the bot will separate it for all members.
            return False
        elif await self._visa_key(user=receiver) is not None:
            # receiver is OK
            return True
        # receiver not ready, suspend message for waiting document
        error = {
            'message': 'encrypt key not found',
            'user': str(receiver),
        }
        self.suspend_instant_message(msg=msg, error=error)  # msg['error'] = error
        return False

    #
    #   Packing
    #

    # Override
    async def encrypt_message(self, msg: InstantMessage) -> Optional[SecureMessage]:
        # 1. check contact info
        # 2. check group members info
        if await self._check_receiver(msg=msg):
            # receiver is ready
            pass
        else:
            self.warning('receiver not ready: %s', msg.receiver)
            return None
        return await super().encrypt_message(msg=msg)

    # Override
    async def verify_message(self, msg: ReliableMessage) -> Optional[SecureMessage]:
        # 1. check receiver/group with local user
        # 2. check sender's meta
        if not await self._check_attachments(msg=msg):
            self.error('message attachments error: %s -> %s: %s', msg.sender, msg.receiver, msg)
            return None
        elif not await self._check_sender(msg=msg):
            self.warning('sender not ready: %s', msg.sender)
            return None
        # make sure sender's meta exists before verifying message
        return await super().verify_message(msg=msg)

    # Override
    async def sign_message(self, msg: SecureMessage) -> ReliableMessage:
        if isinstance(msg, ReliableMessage):
            # already signed
            return msg
        return await super().sign_message(msg=msg)
