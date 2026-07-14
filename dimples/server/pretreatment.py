# -*- coding: utf-8 -*-
# ==============================================================================
# MIT License
#
# Copyright (c) 2026 Albert Moky
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

from typing import Optional, Tuple, List, Set, Dict

from dimsdk import ID, ANYONE, EVERYONE
from dimsdk import EntityType
from dimsdk import ReliableMessage
from dimsdk import TwinsHelper

from ..utils import Log, Logging
from ..common import HandshakeCommand
from ..common import Station
from ..common import CommonFacebook, CommonMessenger
from ..common import CommonMessagePacker

from .cpu import AnsCommandProcessor
from .trace import TraceManager
from .checker import ServerChecker


class Pretreatment(TwinsHelper, Logging):

    @property  # Override
    def facebook(self) -> CommonFacebook:
        barrack = super().facebook
        assert isinstance(barrack, CommonFacebook), f'facebook error: {barrack}'
        return barrack

    @property  # Override
    def messenger(self) -> CommonMessenger:
        transceiver = super().messenger
        assert isinstance(transceiver, CommonMessenger), f'messenger error: {transceiver}'
        return transceiver

    @property
    def message_packer(self) -> CommonMessagePacker:
        packer = self.messenger.packer
        assert isinstance(packer, CommonMessagePacker), f'message packer error: {packer}'
        return packer

    @property
    def entity_checker(self) -> ServerChecker:
        checker = self.facebook.checker
        assert isinstance(checker, ServerChecker), f'entity checker error: {checker}'
        return checker

    #
    #   Results of pretreatment:
    #
    #       msg  - message to this station, None for dropped
    #       list - message to other user(s), waiting to deliver
    #

    async def pretreat(self, msg: ReliableMessage) -> Tuple[Optional[ReliableMessage], List[ReliableMessage]]:
        facebook = self.facebook
        current = await facebook.current_user
        if current is None:
            self.error('failed to get current user')
            return None, []
        #
        #   0. check duplicated
        #
        station = current.identifier
        sender = msg.sender
        receiver = msg.receiver
        if _is_duplicated(msg=msg, node=station):
            self.warning('ignore duplicated message: %s -> %s, %s', sender, receiver, msg.group)
            return None, []
        #
        #   1. check for current station
        #
        if receiver == station:
            # message to this station
            # maybe a meta command, document command, etc ...
            return msg, []
        elif receiver == Station.ANY or receiver == ANYONE:
            # if receiver == 'station@anywhere':
            #     it must be the first handshake without station ID;
            # if receiver == 'anyone@anywhere':
            #     it should be other plain message without encryption.
            return msg, []
        messenger = self.messenger
        session = messenger.session
        #
        #   2. check session
        #
        if session.identifier is None or not session.active:
            # not login?
            # 2.1. suspend this message for waiting handshake
            error = {
                'message': 'user not login',
            }
            packer = self.message_packer
            packer.suspend_reliable_message(msg=msg, error=error)
            # 2.2. ask client to handshake again (with session key)
            #      this message won't be delivered before handshake accepted
            command = HandshakeCommand.ask(session=session.session_key)
            command['force'] = True
            await messenger.send_content(content=command, sender=station, receiver=sender, priority=-1)
            return None, []
        elif receiver == Station.EVERY or receiver == EVERYONE:
            # broadcast message (to neighbor stations)
            # e.g.: 'stations@everywhere', 'everyone@everywhere'
            checker = self.entity_checker
            neighbors = await checker.all_neighbors
            neighbors.discard(station)
            # if receiver == 'everyone@everywhere':
            #     broadcast message to all destinations,
            #     current station is it's receiver too.
            messages = []
            for sid in neighbors:
                msg_info = msg.copy_dict()
                msg_info['group'] = str(receiver)
                msg_info['receiver'] = str(sid)
                r_msg = ReliableMessage.parse(msg=msg_info)
                messages.append(r_msg)
            return msg, messages
        elif receiver.is_broadcast:
            # broadcast message (to station bots)
            # e.g.: 'archivist@anywhere', 'announcer@anywhere', 'monitor@anywhere', ...
            name = receiver.name
            assert name is not None and name != 'station' and name != 'anyone', f'receiver error: {receiver}'
            bot = AnsCommandProcessor.ans_id(name=name)
            if bot is None:
                self.warning('failed to get receiver: %s', receiver)
                return None, []
            elif bot == sender:
                self.warning('skip cycled message: %s -> %s', sender, receiver)
                return None, []
            elif bot == station:
                self.warning('skip current station: %s -> %s', sender, receiver)
                return None, []
            else:
                self.info('forward to bot: %s -> %s', name, bot)
                msg_info = msg.copy_dict()
                msg_info['group'] = str(EVERYONE)
                msg_info['receiver'] = str(bot)
                r_msg = ReliableMessage.parse(msg=msg_info)
            return msg, [r_msg]
        elif receiver.is_group:
            # encrypted group messages should be sent to the group assistant,
            # the station will never process these messages.
            self.error('group message should not send to station: %s, %s -> %s', station, sender, receiver)
            return None, []
        # this message is not for current station,
        # deliver to the real receiver and respond to sender
        user = await facebook.get_user(identifier=receiver)
        if user is None:
            self.error('user not ready: %s', receiver)
            return None, [msg]
        terminal = await user.terminals
        self.info('split message for receiver: %s -> %s', receiver, terminal)
        array = _split_message(msg=msg, receiver=receiver, terminals=terminal)
        return None, array


def _split_message(msg: ReliableMessage, receiver: ID, terminals: Set[str]) -> List[ReliableMessage]:
    candidates = set()
    for target in terminals:
        if target == '' or target == '*':
            did = receiver.without_terminal()
        else:
            did = receiver.with_terminal(terminal=target)
        text = str(did)
        candidates.add(text)
    Log.info('split message for receiver: %s -> %s', receiver, terminals)
    #
    #  get message keys
    #
    msg_keys = msg.get('keys')
    if msg_keys is None:
        key = msg.get('key')
        if key is None:
            msg_keys = {}
        else:
            msg_keys = {
                str(receiver): key,
            }
        md = None
    else:
        assert isinstance(msg_keys, Dict), f'message keys error: {msg_keys}'
        md = msg_keys.get('digest')
        if md is not None:
            msg_keys.pop('digest')
    messages = []
    #
    #  split message for keys
    #
    for key, value in msg_keys.items():
        candidates.discard(key)
        msg_info = msg.copy_dict()
        msg_info['receiver'] = key
        if md is None:
            msg_info['keys'] = {
                key: value,
            }
        else:
            msg_info['keys'] = {
                key: value,
                'digest': md,
            }
        r_msg = ReliableMessage.parse(msg=msg_info)
        messages.append(r_msg)
    #
    #  check for other terminals
    #
    for did in candidates:
        msg_info = msg.copy_dict()
        msg_info['receiver'] = did
        if md is not None:
            msg_info['keys'] = {
                'digest': md,
            }
        r_msg = ReliableMessage.parse(msg=msg_info)
        messages.append(r_msg)
    Log.info('split %d message(s) for receiver: %s; %s + %s', len(messages), receiver, msg_keys.keys(), candidates)
    return messages


def _is_duplicated(msg: ReliableMessage, node: ID) -> bool:
    """ check duplicated message """
    man = TraceManager()
    # check & append current node in msg['traces']
    prev = man.update_traces(msg=msg, node=node)
    man.add_node(msg=msg, node=node)
    if prev is None:
        # previous trace for current node not found
        return False
    sender = msg.sender
    receiver = msg.receiver
    # check cycled message
    if receiver.is_broadcast:
        # ignore cycled broadcast message
        Log.warning('drop cycled broadcast message: %s -> %s', sender, receiver)
        return True
    elif sender.type == EntityType.STATION or receiver.type == EntityType.STATION:
        # ignore cycled station message
        Log.warning('drop cycled station message: %s -> %s', sender, receiver)
        return True
    elif sender.type == EntityType.BOT or receiver.type == EntityType.BOT:
        # ignore cycled bot message
        Log.warning('drop cycled bot message: %s -> %s', sender, receiver)
        return True
    elif msg.time is None:
        Log.error('message time not found: %s -> %s', sender, receiver)
        return True
    # check last time
    delta = msg.time - prev.time
    if delta < 60:
        Log.warning('drop cycled message: %s -> %s', sender, receiver)
        return True
    else:
        Log.info('restart cycled message: %s -> %s', sender, receiver)
        return False
