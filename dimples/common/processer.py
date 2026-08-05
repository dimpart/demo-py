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

from abc import ABC, abstractmethod
from typing import List

from dimsdk import DateTime
from dimsdk import Envelope, Content, ArrayContent, ForwardContent
from dimsdk import InstantMessage, ReliableMessage
from dimsdk import MessageProcessor
from dimsdk import Facebook, Messenger
from dimsdk.cpu import ContentProcessorCreator
from dimsdk.cpu import GeneralContentProcessorFactory

from ..utils import Logging
from .protocol import MessageUtils

from .facebook import CommonFacebook


# noinspection PyAbstractClass
class CommonMessageProcessor(MessageProcessor, Logging, ABC):

    # Override
    def _create_factory(self, facebook: Facebook, messenger: Messenger):
        creator = self._create_creator(facebook=facebook, messenger=messenger)
        return GeneralContentProcessorFactory(creator=creator)

    @abstractmethod
    def _create_creator(self, facebook: Facebook, messenger: Messenger) -> ContentProcessorCreator:
        raise NotImplementedError(
            f'Not implemented: {type(self).__module__}.{type(self).__name__}._create_creator()'
        )

    # Override
    async def process_instant_message(self, msg: InstantMessage, r_msg: ReliableMessage) -> List[InstantMessage]:
        facebook = self.facebook
        transceiver = self.messenger
        assert facebook is not None and transceiver is not None, 'twins not ready'
        # 1. process content from sender
        responses = await transceiver.process_content(content=msg.content, r_msg=r_msg)
        if len(responses) == 0:
            # nothing to respond
            return []
        # 2. select a local user to build message
        sender = MessageUtils.real_sender(msg=msg)
        receiver = MessageUtils.real_receiver(msg=msg)
        user = await self.select_local_user(receiver=receiver)
        if user is None:
            # assert False, f'receiver error: {receiver}'
            return []
        else:
            me = user.identifier
        # 3. pack all responses in one message
        env = Envelope.create(sender=me, receiver=sender)
        if len(responses) == 1:
            body = responses[0]
        else:
            body = ArrayContent.create(contents=responses)
        return [
            InstantMessage.create(head=env, body=body)
        ]

    # Override
    async def process_content(self, content: Content, r_msg: ReliableMessage) -> List[Content]:
        responses = await super().process_content(content=content, r_msg=r_msg)
        cnt = len(responses)
        if cnt > 0 and _contents_empty(contents=responses):
            # remove empty ArrayContent, ForwardContent
            self.warning('drop %d empty response(s): %s -> %s, %s', cnt, r_msg.sender, r_msg.receiver, responses)
            responses = []
        # check sender's document times from the message
        # to make sure the user info synchronized
        await self._check_visa_time(content=content, r_msg=r_msg)
        return responses

    # private
    # noinspection PyUnusedLocal
    async def _check_visa_time(self, content: Content, r_msg: ReliableMessage) -> bool:
        facebook = self.facebook
        assert isinstance(facebook, CommonFacebook), f'facebook error: {facebook}'
        checker = facebook.checker
        if checker is None:
            assert False, 'entity checker lost'
        doc_updated = False
        # check sender document time
        last_doc_time = r_msg.get_datetime(key='SDT')
        if last_doc_time is not None:
            now = DateTime.now()
            if last_doc_time.after(now):
                # calibrate the clock
                last_doc_time = now
            sender = r_msg.sender
            doc_updated = checker.set_last_document_time(identifier=sender, now=last_doc_time)
            # check whether needs update
            if doc_updated:
                self.info('checking for new visa: %s', sender)
                await facebook.get_documents(identifier=sender)
        return doc_updated


def _contents_empty(contents: List[Content]) -> bool:
    for msg_body in contents:
        if not _content_empty(content=msg_body):
            return False
    return True


def _content_empty(content: Content) -> bool:
    if isinstance(content, ArrayContent):
        content.to_map()  # serialize "contents"
        return _contents_empty(contents=content.contents)
    elif isinstance(content, ForwardContent):
        content.to_map()  # serialize "messages"
        return len(content.secrets) == 0
    else:
        return False
