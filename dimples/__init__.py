# -*- coding: utf-8 -*-
#
#   DIMPLES : DIMP Library for Edges and Stations
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

from dimsdk import __all__ as _dimsdk_exports
from dimax import __all__ as _dimax_exports
from dimap import __all__ as _dimap_exports

from .utils import __all__ as _utils_exports

from .common import __all__ as _common_exports
from .conn import __all__ as _conn_exports
from .database import __all__ as _db_exports
from .group import __all__ as _group_exports

from dimsdk import *
from dimax import *
from dimap import *

from .utils import *
from .common import *
from .conn import *
from .database import *
from .group import *

from .emitter import Emitter


name = 'DIMPLES'

__author__ = 'Albert Moky'


_sdk = _dimsdk_exports + _dimax_exports + _dimap_exports
_lib = _utils_exports + _common_exports + _conn_exports + _db_exports + _group_exports

__all__ = list(dict.fromkeys(_sdk + _lib + [

    'Emitter'

]))
