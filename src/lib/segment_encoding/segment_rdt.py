from lib.segment_encoding.header_rdt import HeaderRDT


class SegmentRDT:

    MAX_DATA_SIZE = 1024

    def __repr__(self):
        return "SegmentRDT(header={}, data={})".format(
            self.header, self.data)

    def __str__(self):
        return self.__repr__()

    def __init__(self, header: HeaderRDT, data: bytes):
        self.header: HeaderRDT = header
        self.data = data

    def size(self):
        return HeaderRDT.size() + self.header.data_size

    def as_bytes(self):
        return self.header.as_bytes() + self.data

    def get_max_segment_size(self):
        return self.MAX_DATA_SIZE

    @classmethod
    def from_bytes(cls, data):
        header_size = HeaderRDT.size()

        if len(data) < header_size:
            raise ValueError("Received data size is less than header size")

        header = HeaderRDT.from_bytes(data[:header_size])
        data = data[header_size:]

        # TODO check if data size is correct according with header info

        return cls(header, data)


segment = SegmentRDT
