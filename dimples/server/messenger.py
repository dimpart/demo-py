# -*- coding: utf-8 -*-
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

"""
    Messenger for request handler in station
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Transform and send message
"""

from typing import List, Set

from dimsdk import EntityType
from dimsdk import ID, ANYONE, EVERYONE
from dimsdk import Envelope
from dimsdk import InstantMessage, ReliableMessage

from ..common import DocumentUtils, MessageUtils
from ..common import HandshakeCommand
from ..common import Station
from ..common import CommonMessenger
from ..common import CommonMessagePacker

from .cpu import AnsCommandProcessor

from .checker import ServerChecker


class ServerMessenger(CommonMessenger):

    @CommonMessenger.packer.getter  # Override
    def packer(self) -> CommonMessagePacker:
        delegate = super().packer
        assert isinstance(delegate, CommonMessagePacker), f'message packer error: {delegate}'
        return delegate

    @property
    def entity_checker(self) -> ServerChecker:
        checker = self.facebook.checker
        assert isinstance(checker, ServerChecker), f'entity checker error: {checker}'
        return checker

    # Override
    async def handshake_success(self):
        session = self.session
        identifier = session.identifier
        remote_address = session.remote_address
        self.warning('user login: %s, socket: %s', identifier, remote_address)
        # process suspended messages
        await self._process_suspend_messages()

    async def _process_suspend_messages(self):
        """ process again """
        messages = self.packer.resume_reliable_messages()
        for msg in messages:
            msg.pop('error', None)
            self.info('processing suspended message: %s -> %s', msg.sender, msg.receiver)
            try:
                responses = await self.process_reliable_message(msg=msg)
                for res in responses:
                    await self.send_reliable_message(msg=res, priority=1)
            except Exception as error:
                self.error('failed to process incoming message: %s', error)

    # Override
    async def process_reliable_message(self, msg: ReliableMessage) -> List[ReliableMessage]:
        facebook = self.facebook
        session = self.session
        #
        #   0. check login
        #
        sender = msg.sender
        sess_id = session.identifier
        if sess_id is None:  # or sess_id.is_same_as(other=sender):
            # first handshake?
            visa = MessageUtils.get_visa(msg=msg)
            if visa is not None:
                terminal = DocumentUtils.get_visa_terminal(document=visa)
                self.info('new terminal: "%s", sender: %s', terminal, sender)
                if terminal is None:
                    # old version client (<1.6.0)
                    terminal = ''
                # check old value
                device = session.device
                if device is None:
                    self.info('update session terminal: "%s" -> "%s", sender: %s', device, terminal, sender)
                    session.set_device(terminal=terminal)
                else:
                    # TODO:
                    self.error('session terminal conflicts: "%s" -> "%s", sender: %s', device, terminal, sender)
                    session.set_device(terminal=terminal)
            elif sender.type == EntityType.USER:
                self.error('Please send "handshake" command with visa first: %s, %s', sender, msg)
        #
        #   1. check sender
        #
        if 'from' in msg:
            # A: already exploded
            sender = MessageUtils.send_from(msg=msg)
        elif sess_id is None or sess_id.is_same_as(other=sender):
            # B: user not login yet
            # C: sender is the login-user, not a MTA (redirecting this message)
            terminal = session.device
            # session.device should be set with visa.terminal now
            if terminal is not None:
                # rebuild sender with session.device
                sender = sender.with_terminal(terminal=terminal)
                msg['from'] = f'/{terminal}'
        #
        #   2. check for current station
        #
        receiver = msg.receiver
        current_station = await facebook.current_user
        assert current_station is not None, 'should not happen'
        if receiver == current_station.identifier:
            # message to this station
            # maybe a meta command, document command, etc ...
            return await super().process_reliable_message(msg=msg)
        elif receiver == Station.ANY or receiver == ANYONE:
            # if receiver == 'station@anywhere':
            #     it must be the first handshake without station ID;
            # if receiver == 'anyone@anywhere':
            #     it should be other plain message without encryption.
            return await super().process_reliable_message(msg=msg)
        #
        #   3. check session
        #
        if session.identifier is None or not session.active:
            # not login?
            # 2.1. suspend this message for waiting handshake
            error = {
                'message': 'user not login',
            }
            self.packer.suspend_reliable_message(msg=msg, error=error)
            # 2.2. ask client to handshake again (with session key)
            #      the message above won't be processed before handshake accepted
            body = HandshakeCommand.ask(session=session.session_key)
            head = Envelope.create(sender=current_station.identifier, receiver=sender)
            i_msg = InstantMessage.create(head=head, body=body)
            s_msg = await self.encrypt_message(msg=i_msg)
            if s_msg is not None:
                r_msg = await self.sign_message(msg=s_msg)
                if r_msg is not None:
                    return [r_msg]
            self.error('failed to respond "handshake" command to user: %s, %s', sender, body)
            return []
        #
        #   4. split message
        #
        messages = await self._explode_message(msg=msg, station=current_station.identifier)
        self.warning('explode message to %d piece(s): %s -> %s', len(messages), sender, receiver)
        responses = []
        for msg in messages:
            res = await super().process_reliable_message(msg=msg)
            responses.extend(res)
        return responses

    async def _explode_message(self, msg: ReliableMessage, station: ID) -> List[ReliableMessage]:
        """ split message for the receiver """
        if 'rcpt' in msg:
            # already exploded
            return [msg]
        else:
            sender = msg.sender
            receiver = msg.receiver
        #
        #   explode for all stations
        #
        if receiver == Station.EVERY or receiver == EVERYONE:
            # broadcast message (to neighbor stations)
            # e.g.: 'stations@everywhere', 'everyone@everywhere'
            checker = self.entity_checker
            neighbors = await checker.all_neighbors
            neighbors.add(station)
            # if receiver == 'everyone@everywhere':
            #     broadcast message to all destinations,
            #     current station is it's receiver too.
            messages = []
            for sid in neighbors:
                self.info('explode station message: %s -> %s (%s)', sender, receiver, sid)
                msg_info = msg.copy_map()
                msg_info['rcpt'] = str(sid)
                # msg_info['group'] = str(receiver)
                r_msg = ReliableMessage.parse(msg=msg_info)
                messages.append(r_msg)
            return messages
        #
        #   explode for broadcast message
        #
        if receiver.is_broadcast:
            # broadcast message (to station bots)
            # e.g.: 'archivist@anywhere', 'announcer@anywhere', 'monitor@anywhere', ...
            name = receiver.name
            assert name is not None and name != 'station' and name != 'anyone', f'receiver error: {receiver}'
            bot = AnsCommandProcessor.ans_id(name=name)
            if bot is None:
                self.warning('failed to get receiver: %s', receiver)
                return []
            elif bot == sender:
                self.warning('skip cycled message: %s -> %s', sender, receiver)
                return []
            elif bot == station:
                self.warning('skip current station: %s -> %s', sender, receiver)
                return []
            else:
                self.info('forward to bot: %s -> %s', name, bot)
                msg_info = msg.copy_map()
                msg_info['rcpt'] = str(bot)
                r_msg = ReliableMessage.parse(msg=msg_info)
            return [r_msg]
        elif receiver.is_group:
            # encrypted group messages should be sent to the group assistant,
            # the station will never process these messages.
            self.error('group message should not send to station: %s, %s -> %s', station, sender, receiver)
            return []
        #
        #   explode for user
        #
        facebook = self.facebook
        user = await facebook.get_user(identifier=receiver)
        if user is None:
            self.error('user not ready: %s', receiver)
            return [msg]
        # split message with user terminals
        terminals = await user.terminals
        self.info('split message for receiver: %s -> %s', receiver, terminals)
        return self._split_personal_message(msg=msg, receiver=receiver, terminals=terminals)

    def _split_personal_message(self, msg: ReliableMessage, receiver: ID, terminals: Set[str]) -> List[ReliableMessage]:
        """ split message for all terminals of the user """
        candidates = set()
        for target in terminals:
            if target == '' or target == '*':
                did = receiver.without_terminal()
            else:
                did = receiver.with_terminal(terminal=target)
            text = str(did)
            candidates.add(text)
        self.info('split message for receiver: %s, %s -> %s', receiver, terminals, candidates)
        #
        #   fetch message keys
        #
        msg_keys = msg.get('keys')
        if msg_keys is None:
            base64 = msg.get('key')
            if base64 is None:
                msg_keys = {}
            else:
                text = str(receiver)
                msg_keys = {
                    text: base64,
                }
                if receiver.terminal is not None:
                    # set msg key for receiver without terminal
                    did = receiver.without_terminal()
                    text = str(did)
                    msg_keys[text] = base64
            md = None
        else:
            assert isinstance(msg_keys, dict), f'message keys error: {msg_keys}'
            md = msg_keys.get('digest')
            if md is not None:
                msg_keys.pop('digest')
        messages = []
        #
        #   split message for keys
        #
        for text, base64 in msg_keys.items():
            candidates.discard(text)
            did = ID.parse(identifier=text)
            if did is None:
                self.error('receiver in "msg.keys" error: %s -> %s, %s', text, base64, msg_keys)
                continue
            self.info('explode personal message: %s -> %s (%s)', msg.sender, receiver, text)
            msg_info = msg.copy_map()
            msg_info['rcpt'] = text
            # build 'keys'
            if base64 is None:
                enc_keys = {}
            else:
                enc_keys = {
                    text: base64,
                }
            # set key digest
            if md is not None:
                enc_keys['digest'] = md
            if len(enc_keys) > 0:
                msg_info['keys'] = enc_keys
            else:
                self.warning('message without "keys": %s -> %s, %s', msg.sender, text, msg.group)
            # OK
            r_msg = ReliableMessage.parse(msg=msg_info)
            messages.append(r_msg)
        #
        #  check for other terminals
        #
        for text in candidates:
            did = ID.parse(identifier=text)
            if did is None:
                self.error('receiver for candidate error: %s', text)
                continue
            else:
                base64 = msg_keys.get(text)
                if base64 is None and did.terminal is not None:
                    # get msg key for receiver without terminal
                    other = str(did.without_terminal())
                    base64 = msg_keys.get(other)
            self.info('explode extra message: %s -> %s (%s)', msg.sender, receiver, text)
            msg_info = msg.copy_map()
            msg_info['rcpt'] = text
            # build 'keys'
            if base64 is None:
                enc_keys = {}
            else:
                enc_keys = {
                    text: base64,
                }
            # set key digest
            if md is not None:
                enc_keys['digest'] = md
            if len(enc_keys) > 0:
                msg_info['keys'] = enc_keys
            else:
                self.warning('message without "keys": %s -> %s, %s', msg.sender, text, msg.group)
            # OK
            r_msg = ReliableMessage.parse(msg=msg_info)
            messages.append(r_msg)
        self.info('split %d message(s) for receiver: %s; %s + %s', len(messages), receiver, msg_keys.keys(), candidates)
        return messages
