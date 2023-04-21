
import ctypes

from lib.sockets_rdt.handshake_header import HandshakeHeaderRDT


class TransferInformation():
    def __init__(self, transfer_type, protocol, file_name, file_size, sha1_hash):
        self.transfer_type: ctypes.c_uint8 = transfer_type
        self.protocol: ctypes.c_uint8 = protocol
        self.file_name: str = file_name
        self.file_size: ctypes.c_uint32 = file_size
        self.sha1_hash = sha1_hash

    @classmethod
    def from_handshake_header(cls, header_handshake: HandshakeHeaderRDT):
        return cls(header_handshake.transfer_type,
                   header_handshake.protocol,
                   header_handshake.file_name,
                   header_handshake.file_size,
                   header_handshake.sha1_hash
                   )
