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
    Command Processor for 'handshake'
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Handshake Protocol
"""

from typing import Optional, List

from dimsdk import DateTime
from dimsdk import ID, Visa
from dimsdk import Content
from dimsdk import DocumentCommand
from dimsdk import ReliableMessage

from dimsdk.cpu import BaseCommandProcessor

from ...utils import Log, Logging
from ...common import DocumentUtils, MessageUtils
from ...common import HandshakeCommand
from ...common import CommonFacebook, CommonMessenger
from ...common import Session


class HandshakeCommandProcessor(BaseCommandProcessor, Logging):

    @property  # Override
    def facebook(self) -> CommonFacebook:
        barrack = super().facebook
        assert isinstance(barrack, CommonFacebook), 'facebook error: %s' % barrack
        return barrack

    @property
    def messenger(self) -> CommonMessenger:
        transceiver = super().messenger
        assert isinstance(transceiver, CommonMessenger), 'messenger error: %s' % transceiver
        return transceiver

    # Override
    async def process_content(self, content: Content, r_msg: ReliableMessage) -> List[Content]:
        facebook = self.facebook
        messenger = self.messenger
        session = messenger.session
        assert isinstance(content, HandshakeCommand), 'handshake command error: %s' % content
        #
        #   check command title
        #
        title = content.title
        if title == 'DIM?' or title == 'DIM!':
            # S -> C
            text = 'Command not support.'
            return self._respond_receipt(text=text, envelope=r_msg.envelope, content=content, extra={
                'template': 'Handshake command error: title="${title}".',
                'replacements': {
                    'title': title,
                }
            })
        elif title == HandshakeCommand.SAY_HI:
            # C -> S: Nice to meet you!
            res = HandshakeCommand.respond(session=content.session)
            res['remote_address'] = session.remote_address
            return [res]
        elif title == HandshakeCommand.HI_BACK:
            # just ignore it
            return []
        else:
            # C -> S: Hello world!
            assert 'Hello world!' == title, 'Handshake command error: %s' % content
            sender = r_msg.sender
            # set/update session.terminal(device) with visa.terminal
            visa = MessageUtils.get_visa(msg=r_msg)
            if visa is not None:
                _update_session_terminal(session=session, visa=visa, sender=sender)
        #
        #   check session key
        #
        if session.session_key != content.session:
            # session key not match
            # ask client to sign it with the new session key
            res = HandshakeCommand.again(session=session.session_key)
            res['remote_address'] = session.remote_address
            return [res]
        else:
            # session key match
            self.info('handshake accepted: %s, session: %s', sender, session.session_key)
            # verified success
            await _handshake_accepted(sender=sender, when=content.time, session=session, messenger=messenger)
            res = HandshakeCommand.success(session=session.session_key)
            res['remote_address'] = session.remote_address
        #
        #   check visa terminal
        #
        sess_id = session.identifier
        assert sess_id.is_same_as(other=sender), 'sender error: %s, %s' % (sender, session)
        visa_documents = await _filter_visa_documents(identifier=sess_id, facebook=facebook)
        cnt = len(visa_documents)
        Log.warning('got %d extra visa document(s) after handshake: %s', cnt, sender)
        if cnt == 0:
            return [res]
        else:
            return [
                res,
                # respond with other visa documents
                DocumentCommand.response(documents=visa_documents, identifier=sender),
            ]


def _update_session_terminal(session: Session, visa: Visa, sender: ID) -> bool:
    terminal = DocumentUtils.get_visa_terminal(document=visa)
    Log.info('new terminal: "%s", sender: %s', terminal, sender)
    # check old value
    device = session.device
    if device is None or device == '':
        Log.info('update session terminal (device): "%s" -> "%s", sender: %s', device, terminal, sender)
        session.set_device(terminal=terminal)
        return True
    # TODO:
    Log.error('session terminal (device) conflicts: "%s" -> "%s", sender: %s', device, terminal, sender)
    session.set_device(terminal=terminal)
    return False


async def _handshake_accepted(sender: ID, when: Optional[DateTime], session: Session, messenger: CommonMessenger):
    from ..session_center import SessionCenter
    center = SessionCenter()
    # 1. update session ID
    center.update_session(session=session, identifier=sender)
    # 2. update session flag
    session.set_active(active=True, when=when)
    # 3. callback
    from ..messenger import ServerMessenger
    assert isinstance(messenger, ServerMessenger)
    await messenger.handshake_success()


async def _filter_visa_documents(identifier: ID, facebook: CommonFacebook) -> List[Visa]:
    documents = await facebook.get_documents(identifier=identifier)
    if len(documents) < 1:
        return []
    else:
        terminal = identifier.terminal
    other_visa_documents = []
    for doc in documents:
        if not isinstance(doc, Visa):
            Log.warning('visa document error: %s => %s', identifier, doc)
            continue
        device = DocumentUtils.get_visa_terminal(document=doc)
        if device == terminal:
            # skip for current device
            continue
        Log.info('got another visa (terminal: "%s") for session: %s', device, identifier)
        other_visa_documents.append(doc)
    # OK
    return other_visa_documents
