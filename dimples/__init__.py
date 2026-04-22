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

from dimsdk import *
from dimsdk.cpu import *
from dimplugins import *

from .utils import md5, sha1

from .common import *
from .conn import *
from .database import *
from .group import *

from .emitter import Emitter


name = 'DIMPLES'

__author__ = 'Albert Moky'


__all__ = [

    'Emitter',

    ####################################
    #
    #   SDK
    #
    ####################################

    'Singleton',

    'URI', 'DateTime',

    'Converter', 'DataConverter', 'BaseConverter',

    'Copier',
    'Wrapper', 'Stringer', 'Mapper',
    'ConstantString',  # 'String',
    'Dictionary',

    #
    #   Format
    #

    'DataCoder', 'Hex', 'Base58', 'Base64',
    'ObjectCoder', 'JSON',
    'MapCoder', 'JSONMap',
    'StringCoder', 'UTF8',

    'hex_encode', 'hex_decode',
    'base58_encode', 'base58_decode',
    'base64_encode', 'base64_decode',
    'json_encode', 'json_decode',
    'utf8_encode', 'utf8_decode',

    'TransportableResource',
    'TransportableData',

    'TransportableDataFactory',

    'TransportableDataHelper',
    'FormatExtensions', 'shared_format_extensions',

    'Header', 'DataURI',

    #
    #   TED
    #
    'EncodeAlgorithms',

    'BaseString', 'BaseData',

    'Base64Data', 'PlainData',
    'EmbedData',

    #
    #   PNF
    #
    'TransportableFile', 'TransportableFileFactory',
    'TransportableFileHelper',
    'TransportableFileWrapper', 'TransportableFileWrapperFactory',

    'PortableNetworkFile',
    'PortableNetworkFileWrapper',

    #
    #   Digest
    #

    'MessageDigester',
    'SHA256', 'KECCAK256', 'RIPEMD160',
    # 'MD5', 'SHA1',
    'sha256', 'keccak256', 'ripemd160',
    'md5', 'sha1',

    #
    #   Crypto
    #

    'CryptographyKey',
    'EncryptKey', 'DecryptKey', 'SignKey', 'VerifyKey',
    'SymmetricKey', 'AsymmetricKey',
    'PrivateKey', 'PublicKey',

    'SymmetricKeyFactory', 'PrivateKeyFactory', 'PublicKeyFactory',

    'SymmetricKeyHelper', 'PublicKeyHelper', 'PrivateKeyHelper',
    'CryptoExtensions', 'shared_crypto_extensions',

    #
    #   Algorithms
    #
    'AsymmetricAlgorithms', 'SymmetricAlgorithms',

    #
    #   Ming-Ke-Ming
    #

    'EntityType',
    'Address', 'ID',
    'Meta', 'TAI', 'Document',

    'AddressFactory', 'IDFactory',
    'MetaFactory', 'DocumentFactory',

    'ANYWHERE', 'EVERYWHERE',
    'ANYONE', 'EVERYONE', 'FOUNDER',
    'BroadcastAddress', 'Identifier',

    'AddressHelper', 'IDHelper',
    'MetaHelper', 'DocumentHelper',
    'AccountExtensions', 'shared_account_extensions',

    #
    #   Account Extends
    #

    'GeneralCryptoHelper',
    'GeneralAccountHelper',

    'MetaType',
    'DocumentType',
    'Visa', 'Bulletin',

    #
    #   Dao-Ke-Dao
    #

    'Content', 'Envelope',
    'Message',
    'InstantMessage', 'SecureMessage', 'ReliableMessage',

    'ContentFactory', 'EnvelopeFactory',
    'InstantMessageFactory', 'SecureMessageFactory', 'ReliableMessageFactory',

    'ContentHelper', 'EnvelopeHelper',
    'InstantMessageHelper', 'SecureMessageHelper', 'ReliableMessageHelper',
    'MessageExtensions', 'shared_message_extensions',

    #
    #   Message Extends
    #

    'GeneralMessageHelper',

    'ContentType',

    'Command', 'CommandFactory',
    'CommandHelper', 'GeneralCommandHelper',

    #
    #  Contents
    #

    'TextContent', 'PageContent', 'NameCard',
    'MoneyContent', 'TransferContent',
    'FileContent', 'ImageContent', 'AudioContent', 'VideoContent',
    'ForwardContent', 'CombineContent', 'ArrayContent',
    'QuoteContent',
    'QuoteHelper', 'QuotePurifier',

    #
    #  Commands
    #

    'MetaCommand', 'DocumentCommand',
    'ReceiptCommand',

    'HistoryCommand', 'GroupCommand',
    'InviteCommand', 'ExpelCommand', 'JoinCommand', 'QuitCommand', 'ResetCommand',

    #
    #   Implementations
    #

    'BaseMeta',
    'BaseDocument', 'BaseVisa', 'BaseBulletin',

    #
    #   Contents

    'BaseContent', 'BaseCommand',

    'BaseTextContent', 'WebPageContent', 'NameCardContent',
    'BaseMoneyContent', 'TransferMoneyContent',
    'BaseFileContent', 'ImageFileContent', 'AudioFileContent', 'VideoFileContent',
    'SecretContent', 'CombineForwardContent', 'ListContent',
    'BaseQuoteContent',

    'BaseMetaCommand', 'BaseDocumentCommand',
    'BaseReceiptCommand',
    'BaseHistoryCommand', 'BaseGroupCommand',
    'InviteGroupCommand', 'ExpelGroupCommand', 'JoinGroupCommand', 'QuitGroupCommand', 'ResetGroupCommand',

    #
    #   Messages
    #

    'MessageEnvelope',
    'BaseMessage',
    'PlainMessage', 'EncryptedMessage', 'NetworkMessage',

    ################################################################

    'EncryptedBundle', 'UserEncryptedBundle',
    'EncryptedBundleHelper', 'DefaultBundleHelper',

    'VisaAgent', 'DefaultVisaAgent',

    #
    #   Entities (MingKeMing)
    #

    'EntityDelegate',
    'EntityDataSource',
    'Entity', 'BaseEntity',

    'GroupDataSource',
    'Group', 'BaseGroup',

    'UserDataSource',
    'User', 'BaseUser',

    #
    #   Message Transformers (DaoKeDao)
    #

    'InstantMessageDelegate',
    'SecureMessageDelegate',
    'ReliableMessageDelegate',

    'InstantMessagePacker',
    'SecureMessagePacker',
    'ReliableMessagePacker',

    'MessagePackerFactory',
    'PackerExtensions',

    #
    #   Content Processors (DaoKeDao)
    #

    # 'ContentProcessor',
    # 'ContentProcessorCreator',
    # 'ContentProcessorFactory',
    #
    # 'GeneralContentProcessorFactory',

    #
    #   Core Interfaces
    #

    'Archivist',
    'Barrack',

    'Shortener', 'MessageShortener',
    'Compressor', 'MessageCompressor',

    'Packer',
    'Processor',
    'Transformer',

    'CipherKeyDelegate',

    #
    #   Twins
    #

    'TwinsHelper',

    'Facebook',

    'Messenger',
    'MessageProcessor',
    'MessagePacker',

    ####################################
    #
    #   SDK CPU
    #
    ####################################

    'ContentProcessor',
    'ContentProcessorCreator',
    'ContentProcessorFactory',
    'GeneralContentProcessorFactory',

    #
    #   CPU
    #

    'BaseContentProcessor',
    'BaseCommandProcessor',

    'ArrayContentProcessor',
    'ForwardContentProcessor',

    'MetaCommandProcessor',
    'DocumentCommandProcessor',

    'BaseContentProcessorCreator',

    ####################################
    #
    #   Plugins
    #
    ####################################

    'TransportableDataHelper',
    'FormatExtensions', 'shared_format_extensions',

    'SymmetricKeyHelper', 'PublicKeyHelper', 'PrivateKeyHelper',
    'CryptoExtensions', 'shared_crypto_extensions',

    'AddressHelper', 'IDHelper',
    'MetaHelper', 'DocumentHelper',
    'AccountExtensions', 'shared_account_extensions',

    'GeneralCryptoHelper',
    'GeneralAccountHelper',

    'ContentHelper', 'EnvelopeHelper',
    'InstantMessageHelper', 'SecureMessageHelper', 'ReliableMessageHelper',
    'MessageExtensions', 'shared_message_extensions',

    'GeneralMessageHelper',

    'TransportableFileHelper',

    'CommandHelper', 'GeneralCommandHelper',
    'QuoteHelper', 'QuotePurifier',

    #
    #   Memory Cache
    #

    'MemoryCache',
    'ThanosCache',

    #
    #   Crypto
    #

    'BaseKey',
    'BaseSymmetricKey', 'BaseAsymmetricKey',
    'BasePublicKey', 'BasePrivateKey',

    'PlainKey', 'PlainKeyFactory',
    'AESKey', 'AESKeyFactory',

    'RSAPublicKey', 'RSAPublicKeyFactory',
    'RSAPrivateKey', 'RSAPrivateKeyFactory',

    'ECCPublicKey', 'ECCPublicKeyFactory',
    'ECCPrivateKey', 'ECCPrivateKeyFactory',

    #
    #   Message Digest
    #

    'SHA256Digester', 'KECCAK256Digester', 'RIPEMD160Digester',
    # 'DigestMixIn',

    #
    #   Format
    #

    'Base64Coder', 'Base58Coder', 'HexCoder',
    'JSONCoder', 'UTF8Coder',
    # 'CoderMixIn',

    'BaseNetworkDataFactory', 'BaseNetworkFileFactory',
    # 'TransportableMixIn',

    #
    #   MingKeMing
    #

    'BTCAddress', 'ETHAddress',
    'BaseAddressFactory',

    'GeneralIdentifierFactory',

    'DefaultMeta', 'BTCMeta', 'ETHMeta',
    'BaseMetaFactory',

    'GeneralDocumentFactory',

    #
    #   DaoKeDao
    #

    'GeneralCommandFactory',
    'HistoryCommandFactory',
    'GroupCommandFactory',

    'MessageFactory',

    #
    #   Core Extensions
    #

    'CryptographyKeyGeneralFactory', 'FormatGeneralFactory',
    'AccountGeneralFactory',
    'MessageGeneralFactory', 'CommandGeneralFactory',

    #
    #   Loaders
    #

    'ContentParser', 'CommandParser',
    'ExtensionLoader',
    'PluginLoader',

    ####################################
    #
    #   Common
    #
    ####################################

    'MetaVersion',
    'Password',
    'BroadcastUtils', 'MessageUtils',

    #
    #   Contents
    #

    'AppContent', 'CustomizedContent',
    'AppCustomizedContent',

    #
    #   protocol
    #

    'AnsCommand',

    'HandshakeState', 'HandshakeCommand', 'BaseHandshakeCommand',
    'LoginCommand',

    'BlockCommand',
    'MuteCommand',

    'ReportCommand',

    'HireCommand', 'FireCommand', 'ResignCommand',
    'HireGroupCommand', 'FireGroupCommand', 'ResignGroupCommand',

    'QueryCommand', 'QueryGroupCommand',
    'GroupHistory', 'GroupKeys',

    #
    #   Entities (MingKeMing)
    #

    'EntityDelegate',
    'EntityDataSource',
    'Entity', 'BaseEntity',

    'GroupDataSource',
    'Group', 'BaseGroup',

    'UserDataSource',
    'User', 'BaseUser',

    #
    #   Extends
    #

    'Bot',
    'Station',
    'ServiceProvider',

    #
    #   Utils
    #

    'MetaUtils',
    'DocumentUtils',

    #
    #   Database Interface
    #

    'PrivateKeyDBI', 'MetaDBI', 'DocumentDBI',
    'UserDBI', 'ContactDBI', 'GroupDBI', 'GroupHistoryDBI',
    'AccountDBI',

    'ReliableMessageDBI', 'CipherKeyDBI', 'GroupKeysDBI',
    'MessageDBI',

    'ProviderDBI', 'StationDBI', 'LoginDBI',
    'SessionDBI',

    'ProviderInfo', 'StationInfo',

    #
    #   common
    #

    'Anonymous',
    'AddressNameService', 'AddressNameServer', 'ANSFactory',

    'EntityChecker',
    'CommonArchivist',
    'CommonFacebook',

    'CommonMessenger',
    'CommonMessagePacker',
    'CommonMessageProcessor',
    'SuspendedMessageQueue',

    'Transmitter',
    'Session',

    'Register',

    ####################################
    #
    #   Connection
    #
    ####################################

    'Hub', 'Channel',
    'Connection', 'ConnectionDelegate', 'ConnectionState',
    'BaseChannel',
    'BaseHub', 'BaseConnection', 'ActiveConnection',

    'Ship', 'Arrival', 'Departure', 'DeparturePriority',
    'Porter', 'PorterStatus', 'PorterDelegate', 'Gate',
    'ArrivalShip', 'ArrivalHall', 'DepartureShip', 'DepartureHall',
    'Dock', 'LockedDock', 'StarPorter', 'StarGate',

    #
    #   TCP
    #
    'PlainArrival', 'PlainDeparture', 'PlainPorter',
    'StreamChannel', 'StreamHub', 'TCPServerHub', 'TCPClientHub',

    #
    #   UDP
    #
    'PackageArrival', 'PackageDeparture', 'PackagePorter',
    'PacketChannel', 'PacketHub', 'UDPServerHub', 'UDPClientHub',

    #
    #   Protocol
    #
    'WebSocket', 'NetMsg', 'NetMsgHead', 'NetMsgSeq',

    #
    #   Network
    #
    'WSArrival', 'WSDeparture', 'WSPorter',
    'MarsStreamArrival', 'MarsStreamDeparture', 'MarsStreamPorter',
    'MTPStreamArrival', 'MTPStreamDeparture', 'MTPStreamPorter',
    'FlexiblePorter',
    'CommonGate', 'TCPServerGate', 'TCPClientGate', 'UDPServerGate', 'UDPClientGate',
    # 'GateKeeper',
    'MessageWrapper', 'MessageQueue',
    'BaseSession',

    ####################################
    #
    #   Database
    #
    ####################################

    'PrivateKeyDBI', 'MetaDBI', 'DocumentDBI',
    'UserDBI', 'ContactDBI', 'GroupDBI', 'GroupHistoryDBI',
    'AccountDBI',

    'ReliableMessageDBI', 'CipherKeyDBI', 'GroupKeysDBI',
    'MessageDBI',

    'ProviderDBI', 'StationDBI', 'LoginDBI',
    'SessionDBI',
    'ProviderInfo', 'StationInfo',

    #
    #   DOS
    #

    'Storage',
    'PrivateKeyStorage', 'MetaStorage', 'DocumentStorage',
    'UserStorage', 'GroupStorage', 'GroupHistoryStorage',
    'GroupKeysStorage',
    'LoginStorage',
    'StationStorage',

    #
    #   Redis
    #

    'RedisConnector', 'RedisCache',

    'MetaCache', 'DocumentCache',
    'UserCache', 'LoginCache',
    'GroupCache', 'GroupHistoryCache', 'GroupKeysCache',
    'MessageCache',
    'StationCache',

    #
    #   Table
    #

    'DbTask', 'DataCache',

    'PrivateKeyTable', 'MetaTable', 'DocumentTable',
    'UserTable', 'GroupTable', 'GroupHistoryTable',
    'GroupKeysTable',
    'ReliableMessageTable', 'CipherKeyTable',
    'LoginTable', 'StationTable',

    #
    #   Database
    #

    'AccountDatabase',
    'MessageDatabase',
    'SessionDatabase',

    ####################################
    #
    #   Group
    #
    ####################################

    'TripletsHelper',
    # 'GroupBotsManager',

    'GroupDelegate',
    'GroupPacker',
    'GroupEmitter',

    'GroupCommandHelper',
    'GroupHistoryBuilder',

    'GroupManager',
    'AdminManager',

    'SharedGroupManager',

]
