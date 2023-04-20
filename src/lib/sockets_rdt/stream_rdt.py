

import logging
import socket
from lib.sockets_rdt.handshake_header import HandshakeHeaderRDT
from lib.constant import TransferType

from lib.segment_encoding.header_rdt import HeaderRDT
from lib.segment_encoding.segment_rdt import SegmentRDT


class StreamRDT():

    START_ACK = 1

    CLIENT_HANDSHAKE_TIMEOUT = 1
    MAX_HANDSHAKE_TIMEOUT_RETRIES = 10

    def __init__(self, protocol, sv_host, sv_port, client_host, client_port,
                 seq_num, ack_num):
        self.protocol = protocol
        self.sv_host = sv_host
        self.sv_port = sv_port
        self.client_host = client_host
        self.client_port = client_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('', self.sv_port))
        self.seq_num = seq_num
        self.ack_num = ack_num

    def settimeout(self, seconds):
        self.socket.settimeout(seconds)

    # ======================== FOR PUBLIC USE ========================

    def send(self, data: bytes):
        header = HeaderRDT(self.seq_num, self.ack_num - 1, False, False)
        segment = SegmentRDT(header, data)

        self.socket.sendto(
            segment.as_bytes(),
            (self.client_host, self.client_port)
        )

    def read(self, buf_size) -> SegmentRDT:
        while True:
            try:
                bytes, clientAddress = self.socket.recvfrom(
                    buf_size + HeaderRDT.size())
                if clientAddress[0] != self.client_host or \
                        clientAddress[1] != self.client_port:
                    logging.debug(
                        "Invalid client address received: {}".format(
                            clientAddress)
                    )
                    continue

            except TimeoutError:
                continue

    #   TODO COMPLETAR BIEN
        segment = SegmentRDT.from_bytes(bytes)

        return segment, clientAddress

    def close(self):
        logging.debug("Closing socket")
        self.socket.close()

    # ======================== FOR PRIVATE USE ========================

    def send_handshake_client(self, transfer_type: TransferType):
        handshakeHeader = HandshakeHeaderRDT(
            transfer_type,
            self.protocol, 'nombre',
            1000,
            b'\x02\x80\xf4\xe7\xe0\x17\xfd\x1f\
            \xb0\x85"2\xc6\x94\x1c\x0b\xb9(Y\x0e'
        )
        header = HeaderRDT(HandshakeHeaderRDT.size(),
                           self.seq_num, self.ack_num - 1,
                           True, False)  # Falta hacer header handshake
        segment = SegmentRDT(header, handshakeHeader)

        self.socket.sendto(
            segment.as_bytes(),
            (self.client_host, self.client_port)
        )

    def send_handshake_2(self):
        handshakeHeader = HandshakeHeaderRDT(
            TransferType.UPLOAD, self.protocol, 'nombre',
            1000,
            b'\x02\x80\xf4\xe7\xe0\x17\xfd\x1f\
            \xb0\x85"2\xc6\x94\x1c\x0b\xb9(Y\x0e'
        )
        header = HeaderRDT(
            HandshakeHeaderRDT.size(), self.seq_num,
            self.ack_num - 1,
            True, False
        )  # Falta hacer header handshake
        segment = SegmentRDT(header, handshakeHeader)

        self.socket.sendto(
            segment.as_bytes(),
            (self.client_host, self.client_port)
        )

    def receive_handshake(self):
        data, addr = self.socket.recvfrom(
            SegmentRDT.MAX_SEGMENT_SIZE)  # timer faltaria
        try:
            segment = SegmentRDT.from_bytes(data)
            # check header
            # check addr
        except ValueError:
            logging.debug("Invalid segment received")
        self.update_stream(segment.header)

    def run_handshake_as_client(self, transfer_type: TransferType):
        handshakeHeader = HandshakeHeaderRDT(
            transfer_type,
            self.protocol, 'nombre',
            1000,
            b'\x02\x80\xf4\xe7\xe0\x17\xfd\x1f\
            \xb0\x85"2\xc6\x94\x1c\x0b\xb9(Y\x0e'
        )
        # Create initial message
        header = HeaderRDT(HandshakeHeaderRDT.size(),
                           self.seq_num, self.ack_num - 1,
                           True, False)
        segment = SegmentRDT(header, handshakeHeader.as_bytes())

        # Start message exchange
        retries = 0
        self.socket.settimeout(self.CLIENT_HANDSHAKE_TIMEOUT)
        while retries < self.MAX_HANDSHAKE_TIMEOUT_RETRIES:
            try:
                logging.debug(
                    f"Socket ({self.client_host}:{self.client_port})\
                    sending 1st message of handshake")

                self.socket.sendto(
                    segment.as_bytes(),
                    (self.client_host, self.client_port)
                )

                data, addr = self.socket.recvfrom(
                    SegmentRDT.size()
                )
                segment = SegmentRDT.from_bytes(data)
                # check header
                # check addr
                self.update_stream(segment.header)
                break
            except socket.timeout:
                logging.debug("Timeout, retrying")
                retries += 1

        self.socket.sendto(
            segment.as_bytes(),
            (self.client_host, self.client_port)
        )

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
