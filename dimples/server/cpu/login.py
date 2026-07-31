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
    Command Processor for 'login'
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    login protocol
"""

from typing import List

from dimsdk import ID
from dimsdk import ReliableMessage
from dimsdk import Content

from dimsdk.cpu import BaseCommandProcessor

from ...utils import Logging
from ...common import CommandMessageUtils
from ...common import LoginCommand
from ...common import CommonFacebook, CommonMessenger


class LoginCommandProcessor(BaseCommandProcessor, Logging):

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
    async def process_content(self, content: Content, r_msg: ReliableMessage) -> List[Content]:
        assert isinstance(content, LoginCommand), f'command error: {content}'
        sender = r_msg.sender
        assert sender.is_same_as(other=content.identifier), 'sender not match: %s, %s' % (sender, content.identifier)
        if sender.terminal is None:
            terminal = CommandMessageUtils.get_login_terminal(content=content)
            if terminal is not None:
                sender = sender.with_terminal(terminal=terminal)
        # 1. check roaming station
        station = content.station
        if not isinstance(station, dict):
            self.error('login command error: %s -> %s', sender, content)
            self.error('login command error: %s -> %s', sender, r_msg)
            return []
        # 2. store login command
        session = self.messenger.session
        db = session.database
        if not await db.save_login_command_message(user=sender, content=content, msg=r_msg):
            self.error('login command error/expired: %s', content)
            return []
        current = await self.facebook.current_user
        sid = station.get('did')
        if sid is None:
            sid = station.get('ID')
        roaming = ID.parse(identifier=sid)
        # assert isinstance(roaming, ID), f'login command error: {content}'
        if not isinstance(roaming, ID):
            self.warning('station ID not found: %s', station)
        elif roaming != current.identifier:
            # user roaming to other station
            self.info('user roaming: %s -> %s', sender, roaming)
            # let dispatcher to handle cached messages for roaming user
            add_roaming(user=sender, station=roaming)
            return []
        if sender != session.identifier:
            # forwarded login command
            self.info('user login: %s -> %s, forwarded by %s', sender, roaming, session.identifier)
            return []
        # 3. update session flag
        session.set_active(active=True, when=content.time)
        # only respond the user login to this station
        self.info('user login: %s -> %s', sender, roaming)
        text = 'Login received.'
        return self._respond_receipt(text=text, content=content, envelope=r_msg.envelope, extra={
            'template': 'Login command received: ${did}.',
            'replacements': {
                'did': str(sender),
            }
        })


def add_roaming(user: ID, station: ID):
    """ add roaming user to dispatcher """
    from ..dispatcher import Dispatcher
    dispatcher = Dispatcher()
    dispatcher.add_roaming(user=user, station=station)
