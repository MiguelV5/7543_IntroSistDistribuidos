

from lib.segment_encoding.header_rdt import HeaderRDT


class SegmentRDT:

    MAX_SEGMENT_SIZE = 1024

    def __init__(self, header: HeaderRDT, data: bytes):
        self.header: HeaderRDT = header
        self.data = data

    def size(self):
        return HeaderRDT.size() + self.header.data_size

    def as_bytes(self):
        return self.header.as_bytes() + self.data

    @classmethod
    def from_bytes(cls, data):
        header_size = HeaderRDT.size()
        if data.size() < header_size:
            raise ValueError("Data size is less than header size")
        header = HeaderRDT.from_bytes(data[:header_size])
        data = data[header_size:]
        return cls(header, data)


segment = SegmentRDT
