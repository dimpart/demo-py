# -*- coding: utf-8 -*-
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

import getopt
import sys
from typing import Optional, Tuple, List

OptsPair = Tuple[str, str]
OptsType = List[OptsPair]
ArgsType = List[str]


class SysArgvParser:
    """ Command Line Parser """

    def __init__(self, opts: OptsType, args: ArgsType):
        super().__init__()
        self.__opts = opts
        self.__args = args

    @property
    def opts(self) -> OptsType:
        return self.__opts

    @property
    def args(self) -> ArgsType:
        return self.__args

    def has_opt(self, opt: str) -> bool:
        if not opt.startswith('--'):
            opt = '--' + opt
        opts = self.opts
        for k, _ in opts:
            if k == opt:
                return True
        # not found
        return False

    def get_opt(self, opt: str) -> Optional[str]:
        if not opt.startswith('--'):
            opt = '--' + opt
        opts = self.opts
        for k, v in opts:
            if k == opt:
                return v

    @classmethod
    def parse(cls, shortopts: str, longopts: List[str], argv: List[str] = None):
        if argv is None:
            argv = sys.argv
        try:
            opts, args = getopt.getopt(args=argv[1:],
                                       shortopts=shortopts,
                                       longopts=longopts)
            return SysArgvParser(opts=opts, args=args)
        except getopt.GetoptError:
            # sys.exit(1)
            return None
