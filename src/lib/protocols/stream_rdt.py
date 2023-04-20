

import socket

from lib.segment_handler.header_rdt import HeaderRDT
from lib.segment_handler.segment_rdt import SegmentRDT


class StreamRDT():
    def __init__(self, sv_host, sv_port, client_host, client_port, seq_num, ack_num):
        self.sv_host = sv_host
        self.sv_port = sv_port
        self.client_host = client_host
        self.client_port = client_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('', self.sv_port))
        self.seq_num = seq_num
        self.ack_num = ack_num

    def send(self, data):
        header = HeaderRDT(self.seq_num + 1, self.ack_num, False, False)
        segment = SegmentRDT(header, data)

        self.socket.sendto(
            segment.as_bytes(),
            (self.client_host, self.client_port)
        )

    def send_handshake(self):
        # header = HeaderRDT(self.seq_num + 1, self.ack_num, True, False)
        # segment = SegmentRDT(header, b'')

        # self.socket.sendto(
        #     segment.as_bytes(),
        #     (self.client_host, self.client_port)
        # )

    def receive(self):
        # TODO: generic receive data from client
