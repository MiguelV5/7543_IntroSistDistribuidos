
import ctypes
import struct


class HeaderRDT:

    PACKET_FORMAT = '!III??'

    def __init__(self, data_size, seq_num, ack_num, syn, fin):
        self.data_size: ctypes.c_uint32 = data_size
        self.seq_num: ctypes.c_uint32 = seq_num
        self.ack_num: ctypes.c_uint32 = ack_num
        self.syn: ctypes.c_bool = syn
        self.fin: ctypes.c_bool = fin

    @classmethod
    def size(cls):
        return struct.calcsize(cls.PACKET_FORMAT)

    def as_bytes(self):
        return struct.pack(self.PACKET_FORMAT, self.data_size, self.seq_num,
                           self.ack_num, self.syn, self.fin)

    @classmethod
    def from_bytes(cls, data):
        data_size, seq_num, ack_num, syn, fin = struct.unpack(
            cls.PACKET_FORMAT, data)
        return cls(data_size, seq_num, ack_num, syn, fin)

# Faltaria un protocolo entre Server y Client para que se puedan comunicar sobre si es upload o download/ hash sha1/ tamaño
