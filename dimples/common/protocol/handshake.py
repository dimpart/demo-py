# -*- coding: utf-8 -*-
#
#   DIMP : Decentralized Instant Messaging Protocol
#
#                                Written in 2019 by Moky <albert.moky@gmail.com>
#
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
    Handshake Command Protocol
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    1. (C-S) handshake start
    2. (S-C) handshake again with new session
    3. (C-S) handshake start with new session
    4. (S-C) handshake success
"""

from abc import ABC, abstractmethod
from enum import IntEnum
from typing import Optional

from dimsdk import Command, BaseCommand

from ...utils import StrMap


class HandshakeState(IntEnum):
    Start = 0    # C -> S, without session key(or session expired)
    Again = 1    # S -> C, with new session key
    Restart = 2  # C -> S, with new session key
    Success = 3  # S -> C, handshake accepted


def handshake_state(title: str, session: str = None) -> HandshakeState:
    # Server -> Client
    if title == 'DIM!':  # or title == 'OK!':
        return HandshakeState.Success
    if title == 'DIM?':
        return HandshakeState.Again
    # Client -> Server: "Hello world!"
    if session is None or len(session) == 0:
        return HandshakeState.Start
    else:
        return HandshakeState.Restart


class HandshakeCommand(Command, ABC):
    """
        Handshake Command
        ~~~~~~~~~~~~~~~~~

        data format: {
            type : 0x88,
            sn   : 123,

            command : "handshake",    // command name
            title   : "Hello world!", // "DIM?", "DIM!"
            session : "{SESSION_ID}", // session key
        }
    """
    HANDSHAKE = 'handshake'

    @property
    @abstractmethod
    def title(self) -> str:
        raise NotImplementedError(
            f'Not implemented: {type(self).__module__}.{type(self).__name__}.title getter'
        )

    @property
    @abstractmethod
    def session(self) -> Optional[str]:
        raise NotImplementedError(
            f'Not implemented: {type(self).__module__}.{type(self).__name__}.session getter'
        )

    @property
    @abstractmethod
    def state(self) -> HandshakeState:
        raise NotImplementedError(
            f'Not implemented: {type(self).__module__}.{type(self).__name__}.state getter'
        )

    #
    #   Factories
    #

    @classmethod
    def offer(cls, session: str = None) -> Command:
        """
        Create client-station handshake offer

        :param session: Old session key
        :return: HandshakeCommand object
        """
        return BaseHandshakeCommand(title='Hello world!', session=session)

    @classmethod
    def ask(cls, session: str) -> Command:
        """
        Create station-client handshake again with new session

        :param session: New session key
        :return: HandshakeCommand object
        """
        return BaseHandshakeCommand(title='DIM?', session=session)

    @classmethod
    def accepted(cls, session: str = None) -> Command:
        """
        Create station-client handshake success notice

        :return: HandshakeCommand object
        """
        return BaseHandshakeCommand(title='DIM!', session=session)

    start = offer       # (1. C->S) first handshake, without session
    again = ask         # (2. S->C) ask client to handshake with new session key
    restart = offer     # (3. C->S) handshake with new session key
    success = accepted  # (4. S->C) notice the client that handshake accepted

    #
    #   Test Speed
    #

    SAY_HI = 'Nice to meet you!'
    HI_BACK = 'Nice to meet you too!'

    @classmethod
    def request(cls, session: str = None) -> Command:
        return BaseHandshakeCommand(title=cls.SAY_HI, session=session)

    @classmethod
    def respond(cls, session: str = None) -> Command:
        return BaseHandshakeCommand(title=cls.HI_BACK, session=session)


class BaseHandshakeCommand(BaseCommand, HandshakeCommand):

    def __init__(self, content: StrMap = None, title: str = None, session: str = None):
        if content is None:
            # 1. new command with title & session key
            assert title is not None, f'handshake command error: {session}'
            cmd = self.HANDSHAKE
            super().__init__(cmd=cmd)
            self['title'] = title
            self['message'] = title  # TODO: remove after all clients upgraded
            if session is not None:
                self['session'] = session
        else:
            # 2. command info from network
            assert title is None and session is None, f'params error: {content}, {title}, {session}'
            super().__init__(content)

    @property
    def title(self) -> str:
        return self.get_str(key='title', default='')

    @property
    def session(self) -> Optional[str]:
        return self.get_str(key='session')

    @property
    def state(self) -> HandshakeState:
        return handshake_state(title=self.title, session=self.session)
