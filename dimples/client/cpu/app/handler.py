# -*- coding: utf-8 -*-
#
#   DIM-SDK : Decentralized Instant Messaging Software Development Kit
#
#                                Written in 2022 by Moky <albert.moky@gmail.com>
#
# ==============================================================================
# MIT License
#
# Copyright (c) 2022 Albert Moky
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
from typing import Optional, List, Dict

from dimsdk import ReliableMessage
from dimsdk import Envelope, Content
from dimsdk import ReceiptCommand
from dimsdk import Messenger
from dimsdk.cpu import BaseContentProcessor

from ....common import CustomizedContent


class CustomizedContentHandler(ABC):
    """
        Handler for Customized Content
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    @abstractmethod
    async def handle_action(self, content: CustomizedContent, msg: ReliableMessage,
                            messenger: Messenger) -> List[Content]:
        """
        Do your job

        @param content:   customized content
        @param msg:       network message
        @param messenger: message transceiver
        @return contents
        """
        raise NotImplemented


class BaseCustomizedContentHandler(CustomizedContentHandler):
    """
        Default Handler
        ~~~~~~~~~~~~~~~
    """

    # Override
    async def handle_action(self, content: CustomizedContent, msg: ReliableMessage,
                            messenger: Messenger) -> List[Content]:
        # app = content.application
        app = content.get_str(key='app')
        mod = content.module
        act = content.action
        text = 'Content not support.'
        return self._respond_receipt(text=text, content=content, envelope=msg.envelope, extra={
            'template': 'Customized content (app: ${app}, mod: ${mod}, act: ${act}) not support yet!',
            'replacements': {
                'app': app,
                'mod': mod,
                'act': act,
            }
        })

    #
    #   Convenient responding
    #

    # noinspection PyMethodMayBeStatic
    def _respond_receipt(self, text: str, envelope: Envelope, content: Optional[Content],
                         extra: Optional[Dict] = None) -> List[ReceiptCommand]:
        return [
            # create base receipt command with text & original envelope
            BaseContentProcessor.create_receipt(text=text, envelope=envelope, content=content, extra=extra)
        ]
