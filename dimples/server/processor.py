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

"""
    Server extensions for MessageProcessor
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

from typing import Optional, List

from dimsdk import ID
from dimsdk import EntityType
from dimsdk import InstantMessage, ReliableMessage
from dimsdk import Envelope, Content
from dimsdk import TextContent, ReceiptCommand
from dimsdk import Facebook, Messenger
from dimsdk.cpu import ContentProcessorCreator

from ..common import DocumentUtils, MessageUtils
from ..common import Station
from ..common import CommonFacebook, CommonMessenger
from ..common import CommonMessageProcessor

from .dispatcher import Dispatcher
from .pretreatment import Pretreatment


class ServerMessageProcessor(CommonMessageProcessor):

    def __init__(self, facebook: Facebook, messenger: Messenger):
        super().__init__(facebook=facebook, messenger=messenger)
        self.__pretreatment = Pretreatment(facebook=facebook, messenger=messenger)

    @property
    def facebook(self) -> CommonFacebook:
        barrack = super().facebook
        assert isinstance(barrack, CommonFacebook), f'facebook error: {barrack}'
        return barrack

    @property
    def messenger(self) -> CommonMessenger:
        transceiver = super().messenger
        assert isinstance(transceiver, CommonMessenger), f'messenger error: {transceiver}'
        return transceiver

    # Override
    def _create_creator(self, facebook: Facebook, messenger: Messenger) -> ContentProcessorCreator:
        from .cpu import ServerContentProcessorCreator
        return ServerContentProcessorCreator(facebook=facebook, messenger=messenger)

    # Override
    async def process_content(self, content: Content, r_msg: ReliableMessage) -> List[Content]:
        # process first
        responses = await super().process_content(content=content, r_msg=r_msg)
        # check responses
        contents = []
        sender = r_msg.sender
        from_station = sender.type == EntityType.STATION
        for res in responses:
            if res is None:
                # should not happen
                continue
            elif isinstance(res, ReceiptCommand):
                if from_station:
                    # no need to respond receipt to station
                    self.info('drop receipt to %s, origin msg time=[%s]', sender, r_msg.time)
                    continue
            elif isinstance(res, TextContent):
                if from_station:
                    # no need to respond text message to station
                    self.info('drop text to %s, origin time=[%s], text=%s', sender, r_msg.time, res.text)
                    continue
            contents.append(res)
        # OK
        return contents

    # Override
    async def process_reliable_message(self, msg: ReliableMessage) -> List[ReliableMessage]:
        facebook = self.facebook
        messenger = self.messenger
        session = messenger.session
        current = await facebook.current_user
        sid = current.identifier
        # pretreat
        msg, messages = await self.__pretreatment.pretreat(msg=msg)
        if msg is None:
            responses = []
        else:
            responses = await super().process_reliable_message(msg=msg)
            receiver = msg.receiver
            # check for first handshake
            if receiver == Station.ANY or msg.group == Station.EVERY:
                # if this message sent to 'station@anywhere', or with group ID 'stations@everywhere',
                # it means the client doesn't have the station's meta (e.g.: first handshaking)
                # or visa maybe expired, here attach them to the first response.
                meta = await current.meta
                docs = await current.documents
                visa = DocumentUtils.last_visa(documents=docs)
                for res in responses:
                    if res.sender == sid:
                        # let the first responding message to carry the station's meta & visa
                        MessageUtils.set_meta(meta=meta, msg=res)
                        MessageUtils.set_visa(visa=visa, msg=res)
                        break
            elif session.identifier == sid:
                # station bridge
                responses = await _pick_out(messages=responses, bridge=sid, messenger=messenger)
        # deliver messages
        res = await _deliver_message(messages=messages, station=sid, messenger=messenger)
        responses.extend(res)
        return responses


async def _pick_out(messages: List[ReliableMessage], bridge: ID, messenger: CommonMessenger) -> List[ReliableMessage]:
    responses = []
    roaming_messages = []
    for msg in messages:
        receiver = msg.receiver
        if receiver == bridge:
            # respond to the bridge
            responses.append(msg)
        else:
            # this message is not respond to the bridge, the receiver may be
            # roaming to other station, so deliver it via dispatcher here.
            roaming_messages.append(msg)
    res = await _deliver_message(messages=roaming_messages, station=bridge, messenger=messenger)
    responses.extend(res)
    return responses


async def _deliver_message(messages: List[ReliableMessage], station: ID,
                           messenger: CommonMessenger) -> List[ReliableMessage]:
    respond_messages = []
    dispatcher = Dispatcher()
    for msg in messages:
        sender = msg.sender
        receiver = msg.receiver
        responses = await dispatcher.deliver_message(msg=msg, receiver=receiver)
        for res in responses:
            r_msg = await _pack_message(content=res, sender=station, receiver=sender, messenger=messenger)
            if r_msg is None:
                assert False, f'failed to pack response for: {sender}'
            else:
                respond_messages.append(r_msg)
    return respond_messages


async def _pack_message(content: Content, sender: ID, receiver: ID,
                        messenger: CommonMessenger) -> Optional[ReliableMessage]:
    envelope = Envelope.create(sender=sender, receiver=receiver)
    i_msg = InstantMessage.create(head=envelope, body=content)
    s_msg = await messenger.encrypt_message(msg=i_msg)
    if s_msg is not None:
        return await messenger.sign_message(msg=s_msg)
