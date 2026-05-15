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
    Log Util
    ~~~~~~~~
"""

import logging
import sys

from startrek.types import Log, Logger


class LogLevel:
    """ Logging levels """

    DEBUG: int = logging.DEBUG
    INFO: int = logging.INFO
    WARNING: int = logging.WARNING
    ERROR: int = logging.ERROR

    # DEBUG: int = logging.DEBUG    # 10: debug(), info(), warning(), error()
    DEVELOP: int = logging.INFO     # 20:          info(), warning(), error()
    RELEASE: int = logging.WARNING  # 30:                  warning(), error()


class Logging:
    """ Log MixIn """

    def _format(self, fmt: str) -> str:
        clazz = self.__class__.__name__
        return '%s >\t%s' % (clazz, fmt)

    def debug(self, msg: str, *args, **kwargs):
        msg = self._format(fmt=msg)
        Log.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs):
        msg = self._format(fmt=msg)
        Log.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        msg = self._format(fmt=msg)
        Log.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        msg = self._format(fmt=msg)
        Log.error(msg, *args, **kwargs)


"""
    Colored Log
    ~~~~~~~~~~~
"""


class ColoredFormatter(logging.Formatter):

    _COLORS = {
        logging.DEBUG: '\033[90m',    # grey
        # logging.INFO: '\033[39m',   # foreground
        logging.INFO: None,
        logging.WARNING: '\033[93m',  # yellow
        logging.ERROR: '\033[91m',    # red
    }
    _RESET = '\033[0m'

    def __init__(self, fmt: str = None, datefmt: str = '%Y-%m-%d %H:%M:%S', style: str = '%'):
        super().__init__(fmt=fmt, datefmt=datefmt, style=style)

    # Override
    def format(self, record: logging.LogRecord) -> str:
        _fix_record(record=record)
        text = super().format(record)
        text = _shorten(text=text, max_len=MAX_LOG_LEN)
        color = self._COLORS.get(record.levelno)
        if color is not None:
            reset = self._RESET
            return f'{color}{text}{reset}'
        # text without color
        return text


def _fix_record(record: logging.LogRecord):
    """ Fix for caller """
    frame = logging.currentframe()
    while frame:
        filename = frame.f_code.co_filename
        frame = frame.f_back
        if filename.endswith('types/log.py'):
            if frame is not None:
                filename = frame.f_code.co_filename
                if filename.endswith('utils/log.py'):
                    frame = frame.f_back
            break
    if frame is not None:
        record.module = frame.f_globals.get("__name__", "unknown")
        record.lineno = frame.f_lineno


def _shorten(text: str, max_len: int = 1024) -> str:
    # assert max_len > 128, 'too short: %s' % max_len
    size = 0 if text is None else len(text)
    if size <= max_len:
        return text
    desc = 'total %d chars' % size
    gaps = len(desc) + 10
    pos = max_len - gaps - 32
    return '%s ... %s ... %s' % (text[:pos], desc, text[-32:])


MAX_LOG_LEN = 1024


"""
    Default Logger
    ~~~~~~~~~~~~~~
"""


class StandardLogger(Logger):

    def __init__(self, name: str, fmt: str, level: int):
        super().__init__()
        logger = logging.getLogger(name)
        self.__logger = logger
        if len(logger.handlers) == 0:
            init_log_handlers(logger=logger, fmt=fmt, level=level)

    @property
    def logger(self):
        return self.__logger

    # Override
    def debug(self, msg: str, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)

    # Override
    def info(self, msg: str, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)

    # Override
    def warning(self, msg: str, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)

    # Override
    def error(self, msg: str, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)


def init_log_handlers(logger: logging.Logger, fmt: str, level: int):
    formatter = ColoredFormatter(fmt=fmt)
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(fmt=formatter)  # output format
    handler.setLevel(level=level)        # output level
    logger.setLevel(level=level)         # output level
    logger.addHandler(handler)


def init_logger(name: str, level: int = LogLevel.DEBUG):
    fmt = '%(asctime)s | %(levelname)-8s | %(module)s:%(lineno)d > %(message)s'
    Log.logger = StandardLogger(name=name, fmt=fmt, level=level)
