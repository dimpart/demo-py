# -*- coding: utf-8 -*-
#
#   DIM-SDK : Decentralized Instant Messaging Software Development Kit
#
#                                Written in 2026 by Moky <albert.moky@gmail.com>
#
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

from typing import Optional, Union, Tuple, List
from typing import Mapping

from dimsdk import final

from dimsdk import ID
from dimsdk import ReliableMessage
from dimsdk import Command

from ...utils import list_remove_where
from ...utils import Log

from ..protocol import LoginCommand


@final
class CommandMessageUtils:

    @classmethod
    def get_login_terminal(cls, content: LoginCommand) -> Optional[str]:
        terminal = content.get_str(key='terminal')
        if terminal is None or terminal == '':
            did = content.identifier
            if did is None:
                return None
            terminal = did.terminal
            if terminal is None or terminal == '':
                # '*'
                return None
        # OK
        return terminal

    @classmethod
    def sort_commands(cls, records: List[Tuple[Command, ReliableMessage]]) -> List[Tuple[Command, ReliableMessage]]:
        """ Sort and remove duplicated items """
        records.sort(
            # key=lambda x: -(x[0].time or 0.0)
            key=lambda x: 0.0 if x[0].time is None else -x[0].time
        )
        return records

    @classmethod
    def tidy_commands(cls, records: List[Tuple[Command, ReliableMessage]]) -> List[Tuple[Command, ReliableMessage]]:
        signatures = set()

        def should_remove(pair: Tuple[Command, ReliableMessage]) -> bool:
            cmd = pair[0]
            msg = pair[1]
            # did = cmd.identifier
            did = ID.parse(identifier=cmd.get('did'))
            sig = msg.get_str(key='signature')
            if sig is None or sig in signatures:
                assert sig is not None, f'login command error: {did}, {cmd}'
                Log.warning('skip duplicated command: %s, %s', did, cmd)
                return True
            else:
                signatures.add(sig)
            # TODO: remove expired command(s)
            return False

        list_remove_where(records, predicate=should_remove)
        return records

    #
    #   Local Storage
    #

    @classmethod
    def dump_command_messages(cls, records: List[Tuple[Command, ReliableMessage]]) -> Mapping:
        """ Serialize command messages """
        Log.info('Dump %d command message(s)', len(records))
        # revert command messages
        array = []
        for cmd, msg in records:
            array.append({
                'cmd': cmd.to_map(),
                'msg': msg.to_map(),
            })
        return {
            'records': array,
        }

    @classmethod
    def pump_command_messages(cls, info: Union[Mapping, List]) -> Optional[List[Tuple[Command, ReliableMessage]]]:
        """ Deserialize command messages """
        array = _fetch_command_messages(info=info)
        if array is None:
            return None
        # convert command messages
        records = []
        for item in array:
            cmd = item.get('cmd')
            msg = item.get('msg')
            cmd = Command.parse(content=cmd)
            msg = ReliableMessage.parse(msg=msg)
            if cmd is None or msg is None:
                Log.error('command message error: %s', item)
            else:
                rec = (cmd, msg)
                records.append(rec)
        # done
        Log.info('Pump %d command message(s)', len(records))
        return records


def _fetch_command_messages(info: Union[Mapping, List]) -> Optional[List]:
    if isinstance(info, list):
        return info
    elif isinstance(info, dict):
        records = info.get('records')
        if isinstance(records, list):
            return records
        elif 'cmd' in info and 'msg' in info:
            return [info]
    # error
    Log.error('command messages error: %s', info)
    return None
