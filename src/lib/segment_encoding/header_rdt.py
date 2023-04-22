
import ctypes
import struct
from crc import Calculator, Crc8


calculator = Calculator(Crc8.CCITT, optimized=True)


class HeaderRDT:

    PACKET_FORMAT = '!BIII??'

    CHECKSUM_SIZE = 1

    def __repr__(self):
        return "HeaderRDT(protocol={}, data_size={}, seq_num={}, ack_num={}, syn={}, fin={}, checksum={})".format(  # noqa E501
            self.protocol, self.data_size, self.seq_num, self.ack_num, self.syn, self.fin, self.checksum)

    def __str__(self):
        return self.__repr__()

    def __init__(self,
                 protocol: ctypes.c_uint8,
                 data_size: ctypes.c_uint32,
                 seq_num: ctypes.c_uint32,
                 ack_num: ctypes.c_uint32,
                 syn: ctypes.c_bool,
                 fin: ctypes.c_bool,
                 checksum: ctypes.c_uint8 = None

                 ):
        self.data_size: ctypes.c_uint32 = data_size
        self.protocol: ctypes.c_uint8 = protocol
        self.seq_num: ctypes.c_uint32 = seq_num
        self.ack_num: ctypes.c_uint32 = ack_num
        self.syn: ctypes.c_bool = syn
        self.fin: ctypes.c_bool = fin
        # Not included in struct packing:
        self.checksum: ctypes.c_uint8 = checksum

    @classmethod
    def size(cls):
        return struct.calcsize(cls.PACKET_FORMAT) + cls.CHECKSUM_SIZE

    def as_bytes(self):
        packed_bytes = struct.pack(self.PACKET_FORMAT, self.protocol,
                                   self.data_size,
                                   self.seq_num,
                                   self.ack_num, self.syn, self.fin)
        self.checksum = calculator.checksum(packed_bytes).to_bytes(
            1, byteorder='big'
        )

        return packed_bytes + self.checksum

    @classmethod
    def from_bytes(cls, data):

        if len(data) < cls.size():
            raise ValueError("Received data size is less than header size")

        checksum = data[-1]
        data = data[:-1]

        if calculator.verify(data, checksum) is False:
            raise ValueError("Checksum of HeaderRDT is not correct")

        protocol, data_size, seq_num, ack_num, syn, fin = struct.unpack(
            cls.PACKET_FORMAT, data)

        return cls(protocol, data_size, seq_num, ack_num, syn, fin, checksum)
