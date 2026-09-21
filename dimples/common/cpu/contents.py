# -*- coding: utf-8 -*-
#
#   DIM-SDK : Decentralized Instant Messaging Software Development Kit
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

from typing import List

from dimsdk import ReliableMessage
from dimsdk import Content
from dimsdk import BaseContentProcessor

from dimax import ForwardContent, ArrayContent


class ForwardContentProcessor(BaseContentProcessor):

    # Override
    async def process_content(self, content: Content, r_msg: ReliableMessage) -> List[Content]:
        assert isinstance(content, ForwardContent), f'forward content error: {content}'
        # call messenger to process it
        messenger = self.messenger
        secrets = content.secrets
        responses = []
        for item in secrets:
            results = await messenger.process_reliable_message(msg=item)
            if results is None:
                # assert False, 'should not happen'
                continue
            res = ForwardContent.create(messages=results)
            responses.append(res)
        return responses


class ArrayContentProcessor(BaseContentProcessor):

    # Override
    async def process_content(self, content: Content, r_msg: ReliableMessage) -> List[Content]:
        assert isinstance(content, ArrayContent), f'forward content error: {content}'
        # call messenger to process it
        messenger = self.messenger
        contents = content.contents
        responses = []
        for item in contents:
            results = await messenger.process_content(content=item, r_msg=r_msg)
            if results is None:
                # assert False, 'should not happen'
                res = ArrayContent.create(contents=[])
                # continue
            elif len(results) == 1:
                res = results[0]
            else:
                res = ArrayContent.create(contents=results)
            responses.append(res)
        return responses
