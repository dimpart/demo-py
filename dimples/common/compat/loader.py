# -*- coding: utf-8 -*-
# ==============================================================================
# MIT License
#
# Copyright (c) 2024 Albert Moky
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

from typing import Optional, Any

from dimsdk import Converter, BaseConverter
from dimsdk import DateTime

from dimsdk import ID, Address, Meta, MetaType
from dimsdk import ContentType, Content
from dimsdk import GroupCommand
from dimsdk import AsymmetricAlgorithms
from dimsdk import AsymmetricKey, PrivateKey, PublicKey
from dimplugins import RSAPrivateKeyFactory, RSAPublicKeyFactory
from dimplugins import ExtensionLoader
from dimplugins import PluginLoader

from ...utils.digest import MD5, MD5Digester
from ...utils.digest import SHA1, SHA1Digester

from ..protocol import AppCustomizedContent
from ..protocol import HandshakeCommand, BaseHandshakeCommand
from ..protocol import LoginCommand
from ..protocol import ReportCommand
from ..protocol import AnsCommand
from ..protocol import MuteCommand, BlockCommand
from ..protocol import HireGroupCommand, FireGroupCommand, ResignGroupCommand
from ..protocol import QueryCommand, QueryGroupCommand

from ..ans import AddressNameServer, ANSFactory
from ..facebook import CommonFacebook

from .entity import EntityIDFactory
from .address import CompatibleAddressFactory
from .meta import CompatibleMetaFactory


class LibraryLoader:

    def __init__(self, extensions: ExtensionLoader = None, plugins: PluginLoader = None):
        super().__init__()
        self.__extensions = CommonExtensionLoader() if extensions is None else extensions
        self.__plugins = CommonPluginLoader() if plugins is None else plugins
        self.__loaded = False

    def run(self):
        if self.__loaded:
            # no need to load it again
            return
        else:
            # mark it to loaded
            self.__loaded = True
        # try to load all plugins
        self.load()

    def load(self):
        self.__extensions.load()
        self.__plugins.load()


# noinspection PyMethodMayBeStatic
class CommonExtensionLoader(ExtensionLoader):
    """ Extensions Loader """

    # Override
    def register_id_factory(self):
        ans = AddressNameServer()
        factory = EntityIDFactory()
        ID.set_factory(factory=ANSFactory(factory=factory, ans=ans))
        CommonFacebook.ans = ans

    # Override
    def register_address_factory(self):
        Address.set_factory(factory=CompatibleAddressFactory())

    # Override
    def register_meta_factories(self):
        mkm = CompatibleMetaFactory(version=MetaType.MKM)
        btc = CompatibleMetaFactory(version=MetaType.BTC)
        eth = CompatibleMetaFactory(version=MetaType.ETH)
        Meta.set_factory(version='1', factory=mkm)
        Meta.set_factory(version='2', factory=btc)
        Meta.set_factory(version='4', factory=eth)
        Meta.set_factory(version='mkm', factory=mkm)
        Meta.set_factory(version='btc', factory=btc)
        Meta.set_factory(version='eth', factory=eth)
        Meta.set_factory(version='MKM', factory=mkm)
        Meta.set_factory(version='BTC', factory=btc)
        Meta.set_factory(version='ETH', factory=eth)

    # protected
    def _copy_content_factory(self, msg_type: str, alias: str):
        factory = Content.get_factory(msg_type=msg_type)
        if factory is not None:
            Content.set_factory(msg_type=alias, factory=factory)
        else:
            assert False, 'content factory not exists: %s -> %s' % (msg_type, alias)

    # Override
    def register_content_factories(self):
        super().register_content_factories()
        # Text
        self._copy_content_factory(msg_type=ContentType.TEXT, alias='text')

        # File
        self._copy_content_factory(msg_type=ContentType.FILE, alias='file')
        # Image
        self._copy_content_factory(msg_type=ContentType.IMAGE, alias='image')
        # Audio
        self._copy_content_factory(msg_type=ContentType.AUDIO, alias='audio')
        # Video
        self._copy_content_factory(msg_type=ContentType.VIDEO, alias='video')

        # Web Page
        self._copy_content_factory(msg_type=ContentType.PAGE, alias='page')

        # Name Card
        self._copy_content_factory(msg_type=ContentType.NAME_CARD, alias='card')

        # Quote
        self._copy_content_factory(msg_type=ContentType.QUOTE, alias='quote')

        # Money
        self._copy_content_factory(msg_type=ContentType.MONEY, alias='money')
        self._copy_content_factory(msg_type=ContentType.TRANSFER, alias='transfer')
        # ...

        # Command
        self._copy_content_factory(msg_type=ContentType.COMMAND, alias='command')

        # History Command
        self._copy_content_factory(msg_type=ContentType.HISTORY, alias='history')

        # Content Array
        self._copy_content_factory(msg_type=ContentType.ARRAY, alias='array')

        # Combine and Forward
        self._copy_content_factory(msg_type=ContentType.COMBINE_FORWARD, alias='combine')

        # Top-Secret
        self._copy_content_factory(msg_type=ContentType.FORWARD, alias='forward')

        # Unknown Content Type
        self._copy_content_factory(msg_type=ContentType.ANY, alias='*')

        self.register_customized_factories()

    # protected
    def register_customized_factories(self):
        self._set_content_factory(msg_type=ContentType.APPLICATION, content_class=AppCustomizedContent)

        self._copy_content_factory(msg_type=ContentType.APPLICATION, alias=ContentType.CUSTOMIZED)
        self._copy_content_factory(msg_type=ContentType.APPLICATION, alias='application')
        self._copy_content_factory(msg_type=ContentType.APPLICATION, alias='customized')

    # Override
    def register_command_factories(self):
        super().register_command_factories()
        # Group Admin Commands
        self._set_command_factory(cmd=GroupCommand.HIRE, command_class=HireGroupCommand)
        self._set_command_factory(cmd=GroupCommand.FIRE, command_class=FireGroupCommand)
        self._set_command_factory(cmd=GroupCommand.RESIGN, command_class=ResignGroupCommand)
        # Handshake
        self._set_command_factory(cmd=HandshakeCommand.HANDSHAKE, command_class=BaseHandshakeCommand)
        # Login
        self._set_command_factory(cmd=LoginCommand.LOGIN, command_class=LoginCommand)
        # Report
        self._set_command_factory(cmd=ReportCommand.REPORT, command_class=ReportCommand)
        # ANS
        self._set_command_factory(cmd=AnsCommand.ANS, command_class=AnsCommand)
        # Mute
        self._set_command_factory(cmd=MuteCommand.MUTE, command_class=MuteCommand)
        # Block
        self._set_command_factory(cmd=BlockCommand.BLOCK, command_class=BlockCommand)
        # Group command (deprecated)
        self._set_command_factory(cmd=QueryCommand.QUERY, command_class=QueryGroupCommand)


# noinspection PyMethodMayBeStatic
class CommonPluginLoader(PluginLoader):
    """ Plugin Loader """

    # Override
    def load(self):
        Converter.converter = _SafeConverter()
        super().load()

    # Override
    def _load_message_digesters(self):
        super()._load_message_digesters()
        self.register_md5_digester()
        self.register_sha1_digester()

    # protected
    def register_md5_digester(self):
        MD5.digester = MD5Digester()

    # protected
    def register_sha1_digester(self):
        SHA1.digester = SHA1Digester()

    # protected
    def register_rsa_key_factories(self):
        """ RSA keys with created time """
        # Public Key: RSA
        rsa_pub = RSAPublicKeyFactory()
        PublicKey.set_factory(algorithm=AsymmetricAlgorithms.RSA, factory=rsa_pub)
        PublicKey.set_factory(algorithm='SHA256withRSA', factory=rsa_pub)
        PublicKey.set_factory(algorithm='RSA/ECB/PKCS1Padding', factory=rsa_pub)
        # Private Key: RSA
        rsa_pri = _RSAPrivateKeyFactory()
        PrivateKey.set_factory(algorithm=AsymmetricAlgorithms.RSA, factory=rsa_pri)
        PrivateKey.set_factory(algorithm='SHA256withRSA', factory=rsa_pri)
        PrivateKey.set_factory(algorithm='RSA/ECB/PKCS1Padding', factory=rsa_pri)


class _RSAPrivateKeyFactory(RSAPrivateKeyFactory):

    # Override
    def generate_private_key(self) -> Optional[PrivateKey]:
        pri_key = super().generate_private_key()
        pub_key = pri_key.public_key
        # set created time
        self._set_created_time(key=pri_key)
        self._set_created_time(key=pub_key)
        # OK
        return pri_key

    # noinspection PyMethodMayBeStatic
    def _set_created_time(self, key: AsymmetricKey):
        now = key.get_datetime(key='time')
        if now is None:
            now = DateTime.now()
            key.set_datetime(key='time', value=now)


class _SafeConverter(BaseConverter):

    # Override
    def get_bool(self, value: Any, default: Optional[bool]) -> Optional[bool]:
        try:
            return super().get_bool(value=value, default=default)
        except ValueError:
            return default

    # Override
    def get_int(self, value: Any, default: Optional[int]) -> Optional[int]:
        try:
            return super().get_int(value=value, default=default)
        except ValueError:
            return default

    # Override
    def get_float(self, value: Any, default: Optional[float]) -> Optional[float]:
        try:
            return super().get_float(value=value, default=default)
        except ValueError:
            return default

    # Override
    def get_datetime(self, value: Any, default: Optional[DateTime]) -> Optional[DateTime]:
        try:
            return super().get_datetime(value=value, default=default)
        except ValueError:
            return default
