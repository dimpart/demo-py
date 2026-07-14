# -*- coding: utf-8 -*-
#
#   DIM-SDK : Decentralized Instant Messaging Software Development Kit
#
# ==============================================================================
# MIT License
#
# Copyright (c) 2023 Albert Moky
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

import threading
from typing import Optional, Union, List, Dict

from dimsdk import DateTime
from dimsdk import Mapper, Dictionary
from dimsdk import ID, ReliableMessage

from ..utils import Singleton


class TraceNode(Dictionary):
    """ Trace node with ID and time """

    @property
    def identifier(self) -> ID:
        did = self.get('did')
        if did is None:
            did = self.get('ID')
        return ID.parse(identifier=did)

    @property
    def time(self) -> Optional[DateTime]:
        return self.get_datetime(key='time')

    def __eq__(self, other) -> bool:
        """ Return self == other. """
        if self is other:
            return True
        elif isinstance(other, TraceNode):
            return self.time == other.time and self.identifier == other.identifier
        else:
            return False

    def __ne__(self, other) -> bool:
        """ Return self != other. """
        if self is other:
            return False
        elif isinstance(other, TraceNode):
            return self.time != other.time or self.identifier != other.identifier
        else:
            return True

    def __ge__(self, other) -> bool:
        """ Return self >= other. """
        if self is other:
            return True
        elif isinstance(other, TraceNode):
            return self.time >= other.time

    def __gt__(self, other) -> bool:
        """ Return self > other. """
        if self is other:
            return False
        elif isinstance(other, TraceNode):
            return self.time > other.time

    def __le__(self, other) -> bool:
        """ Return self <= other. """
        if self is other:
            return True
        elif isinstance(other, TraceNode):
            return self.time <= other.time

    def __lt__(self, other) -> bool:
        """ Return self < other. """
        if self is other:
            return False
        elif isinstance(other, TraceNode):
            return self.time < other.time

    @classmethod
    def create(cls, identifier: ID, when: DateTime = None):
        if when is None:
            when = DateTime.now()
        node = {
            'ID': str(identifier),
            'did': str(identifier),
            'time': when.timestamp,
        }
        return cls(dictionary=node)

    @classmethod
    def parse(cls, node: Union[dict, str, None]):  # -> Optional[TraceNode]:
        if node is None:
            return None
        elif isinstance(node, TraceNode):
            return node
        elif isinstance(node, str):
            node = {
                'ID': node,
                'did': node,
            }
        # assert isinstance(node, dict), 'trace node error: %s' % node
        return cls(dictionary=node)

    @classmethod
    def convert(cls, array: List[Union[dict, str]]):  # -> List[TraceNode]:
        nodes = []
        for item in array:
            trace = cls.parse(node=item)
            if trace is not None:
                nodes.append(trace)
        return nodes

    @classmethod
    def revert(cls, nodes: List) -> List[Dict]:
        array = []
        for item in nodes:
            if isinstance(item, Mapper):
                array.append(item.to_dict())
            elif isinstance(item, Dict):
                array.append(item)
            elif isinstance(item, ID):
                array.append({
                    'ID': str(item),
                    'did': str(item),
                })
            elif isinstance(item, str):
                array.append({
                    'ID': item,
                    'did': item,
                })
                # array.append(item)
        return array


class TraceList:
    """ Trace list with message time """

    def __init__(self, msg_time: DateTime, traces: List[TraceNode]):
        super().__init__()
        self.__time = msg_time
        self.__traces = traces

    @property
    def time(self) -> Optional[DateTime]:
        return self.__time

    @property
    def nodes(self) -> List[TraceNode]:
        return self.__traces

    def insert(self, node: TraceNode):
        """ insert trace node with ID and time """
        pos = len(self.__traces) - 1
        while pos >= 0:
            item = self.__traces[pos]
            if item == node:
                # already exists
                return False
            elif item < node:
                # insert after this position
                break
            pos -= 1
        # insert
        self.__traces.insert(pos + 1, node)
        return True

    def last(self, node: ID) -> Optional[TraceNode]:
        """ search for node ID """
        last_item = None
        last_time = None
        for item in self.__traces:
            if item.identifier != node:
                continue
            item_time = item.time
            if last_item is None or last_time is None:
                last_item = item
                last_time = item_time
            elif item_time is not None and item_time > last_time:
                last_item = item
                last_time = item_time
        return last_item


class TracePool:
    """ Trace pool for messages """

    EXPIRES = 3600 * 5

    def __init__(self):
        super().__init__()
        self._next_time = 0
        self.__caches: Dict[str, TraceList] = {}  # signature:receiver => TraceList

    def purge(self, now: DateTime):
        """ remove expired traces """
        if isinstance(now, DateTime):
            now = now.timestamp
        if now < self._next_time:
            return False
        else:
            # purge it next hour
            self._next_time = now + 3600
        expired = now - self.EXPIRES
        keys = set(self.__caches.keys())
        for tag in keys:
            cached = self.__caches.get(tag)
            if cached is None or cached.time < expired:
                self.__caches.pop(tag, None)
        return True

    def get_traces(self, msg: ReliableMessage) -> TraceList:
        """ get traces for this message """
        sig = msg.get('signature')
        assert sig is not None, 'message error: %s' % msg
        if len(sig) > 16:
            sig = sig[-16:]
        add = msg.receiver.address
        tag = '%s:%s' % (sig, add)
        cached = self.__caches.get(tag)
        if cached is None:
            # cache not found, create a new one with message time
            when = msg.time
            cached = TraceList(msg_time=when, traces=[])
            self.__caches[tag] = cached
        return cached

    def add_traces(self, msg: ReliableMessage) -> TraceList:
        """ add traces from msg """
        cached = self.get_traces(msg=msg)
        traces = msg.get('traces')
        if traces is not None:
            array = TraceNode.convert(array=traces)
            for item in array:
                cached.insert(node=item)
        return cached

    def add_trace_node(self, msg: ReliableMessage, node: TraceNode) -> TraceList:
        """ add trace node """
        cached = self.get_traces(msg=msg)
        cached.insert(node=node)
        return cached


class LockedPool(TracePool):

    def __init__(self):
        super().__init__()
        self.__lock = threading.Lock()

    # Override
    def purge(self, now: DateTime):
        if now < self._next_time:
            # we can treat the msg.time as real time for initial checking
            return False
        # if message time out, check with real time
        now = DateTime.now()
        with self.__lock:
            super().purge(now=now)

    # Override
    def get_traces(self, msg: ReliableMessage) -> TraceList:
        with self.__lock:
            return super().get_traces(msg=msg)


@Singleton
class TraceManager:

    def __init__(self):
        super().__init__()
        self.__pool = LockedPool()

    def update_traces(self, msg: ReliableMessage, node: ID) -> Optional[TraceNode]:
        """ merge traces from msg into cached pool,
            remove expired traces, and return the last record for current station
        """
        pool = self.__pool
        cached = pool.add_traces(msg=msg)
        last = cached.last(node=node)
        pool.purge(now=msg.time)  # call when verifying new message
        return last

    # def set_nodes(self, msg: ReliableMessage, nodes: Set[ID]):
    #     """ merge traces from msg into cached pool,
    #         after that, check for these nodes, append them if not exists,
    #         and then update traces in msg
    #     """
    #     now = DateTime.now()
    #     pool = self.__pool
    #     cached = pool.get_traces(msg=msg)
    #     for item in nodes:
    #         last = cached.last(node=item)
    #         if last is None:
    #             cached.insert(node=TraceNode.create(identifier=item, when=now))
    #     msg['traces'] = TraceNode.revert(nodes=cached.nodes)

    def add_node(self, msg: ReliableMessage, node: ID):
        """ append this node into cached list,
            and then update traces in msg
        """
        pool = self.__pool
        cached = pool.add_trace_node(msg=msg, node=TraceNode.create(identifier=node))
        msg['traces'] = TraceNode.revert(nodes=cached.nodes)
