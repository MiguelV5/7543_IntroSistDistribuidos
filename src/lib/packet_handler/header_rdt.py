
import ctypes
import struct


class HeaderRDT:

    PACKET_FORMAT = '!II?'

    def __init__(self, seq_num, ack_num, fin):
        self.seq_num: ctypes.c_uint32 = seq_num
        self.ack_num: ctypes.c_uint32 = ack_num
        self.fin: ctypes.c_bool = fin

    @classmethod
    def size():
        return struct.calcsize()

    def as_bytes(self):
        return struct.pack(self.PACKET_FORMAT, self.seq_num,
                           self.ack_num, self.fin)

    @classmethod
    def from_bytes(cls, data):
        seq_num, ack_num, fin = struct.unpack(cls.PACKET_FORMAT, data)
        return cls(seq_num, ack_num, fin)
