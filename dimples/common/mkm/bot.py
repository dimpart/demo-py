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

"""
    Bot User
    ~~~~~~~~
"""

from typing import Optional

from dimsdk import ID, EntityType
from dimsdk import Document
from dimsdk import BaseUser

from .utils import DocumentUtils


class Bot(BaseUser):

    def __init__(self, identifier: ID):
        super().__init__(identifier=identifier)
        assert identifier.type == EntityType.BOT, 'Bot ID type error: %s' % identifier

    @property
    async def profile(self) -> Optional[Document]:
        """ Bot Document """
        docs = await self.documents
        return DocumentUtils.last_visa(documents=docs)

    @property
    async def provider(self) -> Optional[ID]:
        doc = await self.profile
        if doc is not None:
            icp = doc.get_property(name='provider')
            return ID.parse(identifier=icp)
