
import ctypes

from lib.sockets_rdt.application_header import ApplicationHeaderRDT


class TransferInformation():
    def __init__(self, transfer_type, protocol, file_name, file_size, sha1_hash):
        self.transfer_type: ctypes.c_uint8 = transfer_type
        self.protocol: ctypes.c_uint8 = protocol
        self.file_name: str = file_name
        self.file_size: ctypes.c_uint32 = file_size
        self.sha1_hash = sha1_hash

    @classmethod
    def from_app_header(cls, header_app: ApplicationHeaderRDT):
        return cls(header_app.transfer_type,
                   header_app.protocol,
                   header_app.file_name,
                   header_app.file_size,
                   header_app.sha1_hash
                   )
