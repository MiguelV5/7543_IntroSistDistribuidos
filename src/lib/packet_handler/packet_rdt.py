
from src.lib.packet_handler.header_rdt import HeaderRDT


class SegmentRDT:

    def __init__(self, header, data):
        self.header: HeaderRDT = header
        self.data = data

    def as_bytes(self):
        return self.header.as_bytes() + self.data

    @classmethod
    def from_bytes(cls, data):
        header_size = HeaderRDT.size()
        header = HeaderRDT.from_bytes(data[:header_size])
        data = data[header_size:]
        return cls(header, data)


segment = SegmentRDT
