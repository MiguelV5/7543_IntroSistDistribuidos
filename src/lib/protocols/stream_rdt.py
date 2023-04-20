

import logging
import socket
from lib.application_layer.handshake_header import HandshakeHeaderRDT
from lib.constant import TransferType

from lib.segment_handler.header_rdt import HeaderRDT
from lib.segment_handler.segment_rdt import SegmentRDT


class StreamRDT():

    START_ACK = 1

    def __init__(self, protocol, sv_host, sv_port, client_host, client_port, seq_num, ack_num):
        self.protocol = protocol
        self.sv_host = sv_host
        self.sv_port = sv_port
        self.client_host = client_host
        self.client_port = client_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('', self.sv_port))
        self.seq_num = seq_num
        self.ack_num = ack_num

    def send(self, data):
        header = HeaderRDT(self.seq_num, self.ack_num - 1, False, False)
        segment = SegmentRDT(header, data)

        self.socket.sendto(
            segment.as_bytes(),
            (self.client_host, self.client_port)
        )

    def send_handshake_client(self, transfer_type: TransferType):
        handshakeHeader = HandshakeHeaderRDT(transfer_type, self.protocol, 'nombre',
                                             1000, b'\x02\x80\xf4\xe7\xe0\x17\xfd\x1f\xb0\x85"2\xc6\x94\x1c\x0b\xb9(Y\x0e')
        header = HeaderRDT(HandshakeHeaderRDT.size(), self.seq_num, self.ack_num - 1,
                           True, False)  # Falta hacer header handshake
        segment = SegmentRDT(header, handshakeHeader)

        self.socket.sendto(
            segment.as_bytes(),
            (self.client_host, self.client_port)
        )

    def send_handshake_2(self):
        handshakeHeader = HandshakeHeaderRDT(TransferType.UPLOAD, self.protocol, 'nombre',
                                             1000, b'\x02\x80\xf4\xe7\xe0\x17\xfd\x1f\xb0\x85"2\xc6\x94\x1c\x0b\xb9(Y\x0e')
        header = HeaderRDT(HandshakeHeaderRDT.size(), self.seq_num, self.ack_num - 1,
                           True, False)  # Falta hacer header handshake
        segment = SegmentRDT(header, handshakeHeader)

        self.socket.sendto(
            segment.as_bytes(),
            (self.client_host, self.client_port)
        )

    def receive_handshake(self):
        data, addr = self.socket.recvfrom(
            SegmentRDT.MAX_LENGTH)  # timer faltaria
        try:
            segment = SegmentRDT.from_bytes(data)
            # check header
            # check addr
        except ValueError:
            logging.debug("Invalid segment received")
        self.update_stream(segment.header)

    def update_stream(self, header: HeaderRDT):
        if (header.seq_num > self.ack_num):
            self.ack_num = header.seq_num


stream = StreamRDT("localhost", 5000, "localhost",
                   5001, 999, StreamRDT.START_ACK)
stream.send_handshake()
stream.receive_handshake()
stream.send_handshake()


# Cliente -> ACK: 0,            SQN: 999 ,     DATA: ""
# Server  -> ACK: 999  - 1,     SQN: 2011,     DATA: ""
# Cliente -> ACK: 2011 - 1,     SQN: 999 ,     DATA: ""

# Server  -> ACK: 999  - 1,     SQN: 2011,      DATA: "a"
# Cliente -> ACK: 2011 - 1,     SQN: 999  + 1,  DATA: "b"
# Server  -> ACK: 1000 - 1,     SQN: 2011 + 1,  DATA: "a"
# Cliente -> ACK: 2011 - 1,     SQN: 999  + 1,  DATA: "b"
# Server  -> ACK: 1000 - 1,     SQN: 2011 + 1,  DATA: "a"
# Cliente -> ACK: 2011 - 1,     SQN: 999  + 1,  DATA: "b"
