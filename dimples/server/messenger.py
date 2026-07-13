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

from ..common import CommonMessenger
from ..common import CommonMessagePacker


class ServerMessenger(CommonMessenger):

    # Override
    async def handshake_success(self):
        session = self.session
        identifier = session.identifier
        remote_address = session.remote_address
        self.warning('user login: %s, socket: %s', identifier, remote_address)
        # process suspended messages
        await self._process_suspend_messages()

    async def _process_suspend_messages(self):
        packer = self.packer
        assert isinstance(packer, CommonMessagePacker), f'message packer error: {packer}'
        messages = packer.resume_reliable_messages()
        for msg in messages:
            msg.pop('error', None)
            self.info('processing suspended message: %s -> %s', msg.sender, msg.receiver)
            try:
                responses = await self.process_reliable_message(msg=msg)
                for res in responses:
                    await self.send_reliable_message(msg=res, priority=1)
            except Exception as error:
                self.error('failed to process incoming message: %s', error)
