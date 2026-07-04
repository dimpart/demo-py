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

from typing import Optional, Union, Tuple, List, Dict

from dimsdk import ID
from dimsdk import ReliableMessage
from dimsdk import Command

from ...utils import Log


class CommandMessageUtils:

    @classmethod
    def get_terminal(cls, content: Command) -> Optional[str]:
        terminal = content.get_str(key='terminal')
        if terminal is not None and len(terminal) > 0:
            return terminal
        did = ID.parse(identifier=content.get('did'))
        if did is not None:
            return did.terminal

    @classmethod
    def dump_command_messages(cls, records: List[Tuple[Command, ReliableMessage]]) -> Dict:
        """ Serialize command messages """
        # sort and remove duplicated item
        results = _sort_commands(records=records)
        Log.info('Dump %d/%d command message(s)', len(results), len(records))
        # revert command messages
        array = []
        for cmd, msg in results:
            array.append({
                'cmd': cmd.to_dict(),
                'msg': msg.to_dict(),
            })
        return {
            'records': array,
        }

    @classmethod
    def pump_command_messages(cls, info: Union[Dict, List]) -> Optional[List[Tuple[Command, ReliableMessage]]]:
        """ Deserialize command messages """
        array = _fetch_command_messages(info=info)
        if array is not None:
            records = []
            # convert command messages
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
            # sort and remove duplicated item
            results = _sort_commands(records=records)
            Log.info('Pump %d/%d command message(s)', len(results), len(records))
            return results


def _fetch_command_messages(info: Union[Dict, List]) -> Optional[List]:
    if isinstance(info, List):
        return info
    elif isinstance(info, Dict):
        records = info.get('records')
        if isinstance(records, List):
            return records
        elif 'cmd' in info and 'msg' in info:
            return [info]
    # error
    Log.error('command messages error: %s', info)
    return None


def _sort_commands(records: List[Tuple[Command, ReliableMessage]]) -> List[Tuple[Command, ReliableMessage]]:
    # 1. sort by time DESC
    sorted_records = sorted(
        records,
        # key=lambda x: -(x[0].time or 0.0)
        key=lambda x: 0.0 if x[0].time is None else -float(x[0].time)
    )
    # 2. remove duplicated item
    numbers = set()
    array = []
    for cmd, msg in sorted_records:
        # check serial number
        sn = cmd.sn
        if sn in numbers:
            Log.warning('skip duplicated command: %s, %s', sn, cmd)
            continue
        else:
            numbers.add(sn)
        # next document
        array.append((cmd, msg))
    # done
    return array
