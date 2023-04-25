from lib.segment_encoding.header_rdt import HeaderRDT


class SegmentRDT:
    MAX_DATA_SIZE = 1024

    def __repr__(self):
        return "SegmentRDT(header={}, data_size={})".format(
            self.header, len(self.data))

    def __str__(self):
        return self.__repr__()

    def __init__(self, header: HeaderRDT, data: bytes):
        self.header: HeaderRDT = header
        self.data = data

    def size(self):
        return HeaderRDT.size() + self.header.data_size

    def as_bytes(self):
        return self.header.as_bytes() + self.data

    @classmethod
    def get_max_segment_size(cls):
        return cls.MAX_DATA_SIZE

    @classmethod
    def from_bytes(cls, data):
        header_size = HeaderRDT.size()

        if len(data) < header_size:
            raise ValueError(
                "[SEGMENT] Received data size is less than header size")

        header = HeaderRDT.from_bytes(data[:header_size])
        data = data[header_size:]

        return cls(header, data)
