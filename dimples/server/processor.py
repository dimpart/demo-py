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

from typing import List

from dimsdk import ID
from dimsdk import EntityType
from dimsdk import InstantMessage, ReliableMessage
from dimsdk import Envelope, Content
from dimsdk import TextContent, ReceiptCommand
from dimsdk import Facebook, Messenger
from dimsdk.cpu import ContentProcessorCreator

from ..utils import Log
from ..utils import get_msg_info

from ..common import DocumentUtils, MessageUtils
from ..common import Station
from ..common import CommonFacebook, CommonMessenger
from ..common import CommonMessageProcessor

from .dispatcher import Dispatcher
from .trace import TraceManager


class ServerMessageProcessor(CommonMessageProcessor):

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
        if _is_duplicated(msg=msg, node=sid):
            self.warning('ignore duplicated message: %s -> %s, %s', msg.sender, msg.receiver, msg.group)
            return []
        else:
            rcpt = MessageUtils.real_receiver(msg=msg)
            is_mine = rcpt.is_broadcast or rcpt == sid
        if not is_mine:
            # deliver messages
            return await _deliver_message(messages=[msg], station=sid, messenger=messenger)
        else:
            # 'station@anywhere'
            # 'anyone@anywhere'
            # 'stations@everywhere'
            # 'everyone@everywhere'
            responses = await super().process_reliable_message(msg=msg)
            # check for first handshake
            receiver = msg.receiver
            if receiver == Station.ANY or receiver == Station.EVERY or msg.group == Station.EVERY:
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
        return responses


def _is_duplicated(msg: ReliableMessage, node: ID) -> bool:
    """ check duplicated message """
    man = TraceManager()
    # check & append current node in msg['traces']
    prev = man.update_traces(msg=msg, node=node)
    man.add_node(msg=msg, node=node)
    if prev is None:
        # previous trace for current node not found
        return False
    else:
        sender = msg.sender
        receiver = msg.receiver
        msg_info = get_msg_info(msg=msg)
    # check cycled message
    if receiver.is_broadcast:
        # ignore cycled broadcast message
        Log.warning('drop cycled broadcast message: %s', msg_info)
        return True
    elif receiver.is_group:
        Log.error('drop cycled group message: %s', msg_info)
        return True
    elif sender.type == EntityType.STATION or receiver.type == EntityType.STATION:
        # ignore cycled station message
        Log.warning('drop cycled station message: %s', msg_info)
        return True
    elif sender.type == EntityType.BOT or receiver.type == EntityType.BOT:
        # ignore cycled bot message
        Log.warning('drop cycled bot message: %s', msg_info)
        return True
    # check message time
    msg_time = msg.time
    if msg_time is None:
        rcpt = MessageUtils.rcpt_to(msg=msg)
        Log.error('message time not found: %s -> %s (%s)', sender, receiver, rcpt)
        return True
    # check last time
    delta = msg_time - prev.time
    if delta < 60:
        Log.warning('drop cycled message: %s', msg_info)
        return True
    else:
        Log.info('restart cycled message: %s', msg_info)
        return False


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
        sender = MessageUtils.real_sender(msg=msg)
        receiver = MessageUtils.real_receiver(msg=msg)
        # delivering
        responses = await dispatcher.deliver_message(msg=msg, receiver=receiver)
        for body in responses:
            head = Envelope.create(sender=station, receiver=sender)
            i_msg = InstantMessage.create(head=head, body=body)
            s_msg = await messenger.encrypt_message(msg=i_msg)
            if s_msg is not None:
                r_msg = await messenger.sign_message(msg=s_msg)
                if r_msg is not None:
                    respond_messages.append(r_msg)
                    continue
            Log.error('failed to pack response for: %s, from: %s', sender, station)
    return respond_messages
