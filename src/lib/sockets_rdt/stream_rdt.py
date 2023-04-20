

import logging
import random
import socket
from lib.sockets_rdt.handshake_header import HandshakeHeaderRDT
from lib.constant import DEFAULT_TIMEOUT, TransferType

from lib.segment_encoding.header_rdt import HeaderRDT
from lib.segment_encoding.segment_rdt import SegmentRDT


class StreamRDT():

    START_ACK = 0

    MAX_HANDSHAKE_TIMEOUT_RETRIES = 5
    MAX_READ_TIMEOUT_RETRIES = 3

    def __init__(self, protocol, external_host, external_port, host, port,
                 seq_num, ack_num):
        self.protocol = protocol
        self.external_host = external_host
        self.external_port = external_port
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('', self.port))
        self.socket.settimeout(DEFAULT_TIMEOUT)

        self.seq_num = seq_num
        self.ack_num = ack_num

    @classmethod
    def from_listener(
        cls, protocol, external_host, external_port, host, port,
        segment: SegmentRDT
    ):
        stream = cls(
            protocol, external_host, external_port, host,
            port, random.randint(0, 2**31), segment.header.ack_num
        )

        handshake_header = HandshakeHeaderRDT.from_bytes(segment.data)
        stream.run_handshake_as_listener(handshake_header)
        return stream

    @classmethod
    def connect(
        cls, protocol, external_host,
        external_port, port, transfer_type
    ):
        stream = cls(
            protocol, external_host, external_port, 'localhost',
            port, random.randint(0, 2**31),
            StreamRDT.START_ACK
        )
        logging.error("Connecting to {}:{} with my port: {}".format(
            external_host, external_port, port))
        # stream.socket.bind(('localhost', stream.port))
        stream.run_handshake_as_initiator(transfer_type)
        return stream

    def settimeout(self, seconds):
        self.socket.settimeout(seconds)

    # ======================== FOR PUBLIC USE ========================

    def send(self, data: bytes):
        self._send_base(data, False, False)

    def read(self, buf_size) -> bytes:
        retries = 0
        while retries < self.MAX_READ_TIMEOUT_RETRIES:
            try:
                segment_as_bytes, external_address = self.socket.recvfrom(
                    buf_size + HeaderRDT.size())
                segment = SegmentRDT.from_bytes(segment_as_bytes)
                self._check_address(segment.header, external_address)
                self._update_stream(segment.header)
                return segment.data
            except TimeoutError:
                retries += 1
                logging.debug("Timeout while reading")
                continue
            except ValueError:
                retries += 1
                logging.debug("Invalid segment received")
                continue

    def close(self):
        logging.debug("Closing socket")
        self.socket.close()

    def _check_address(self, header: HeaderRDT, external_address):
        if external_address[0] != self.external_host:
            raise ValueError("Invalid external host")
        if external_address[1] != self.external_port:
            raise ValueError("Invalid external_port")

        # TODO Capaz despues checkear algun checksum

    # ======================== FOR PRIVATE USE ========================

    def _send_base(self, data: bytes, syn, fin):
        header = HeaderRDT(len(data), self.seq_num, self.ack_num, syn, fin)
        segment = SegmentRDT(header, data)

        self.socket.sendto(
            segment.as_bytes(),
            (self.external_host, self.external_port)
        )

    # ---- Handshake related ----

    def _send_handshake(self, data):
        self._send_base(data, True, False)

    def _read_handshake(self):
        data = self.read(HandshakeHeaderRDT.size())
        segment = SegmentRDT.from_bytes(data)
        return HandshakeHeaderRDT.from_bytes(segment.data)

    def _base_handshake_messages_exchange(self, initial_handshake_header):
        self._send_handshake(initial_handshake_header.as_bytes())
        received_handshake_header = self._read_handshake()
        if not initial_handshake_header.equals(received_handshake_header):
            raise ValueError("Handshake failed")

    def _client_handshake_messages_exchange(self, handshake_header_client):
        self._base_handshake_messages_exchange(handshake_header_client)
        self._send_handshake(handshake_header_client.as_bytes())

    def _server_handshake_messages_exchange(
        self, initial_handshake_header_client
    ):
        self._base_handshake_messages_exchange(initial_handshake_header_client)

    #
    def run_handshake_as_initiator(self, transfer_type: TransferType):
        handshake_header_client = HandshakeHeaderRDT(
            transfer_type,
            self.protocol, 'nombre',
            1000,
            b'\x02\x80\xf4\xe7\xe0\x17\xfd\x1f\
            \xb0\x85"2\xc6\x94\x1c\x0b\xb9(Y\x0e'
        )

        # Start message exchange
        retries = 0
        while retries < self.MAX_HANDSHAKE_TIMEOUT_RETRIES:
            try:
                self._client_handshake_messages_exchange(
                    handshake_header_client)
            except TimeoutError:
                logging.debug("Timeout, retrying")
                retries += 1
            except ValueError:
                logging.debug("Invalid packet retrying")
                retries += 1

    #
    def run_handshake_as_listener(
            self, handshake_header_client: HandshakeHeaderRDT
    ):

        # Start message exchange
        retries = 0
        while retries < self.MAX_HANDSHAKE_TIMEOUT_RETRIES:
            try:
                self._server_handshake_messages_exchange(
                    handshake_header_client)
            except TimeoutError:
                logging.debug("Timeout, retrying")
                retries += 1
            except ValueError:
                logging.debug("Invalid packet retrying")
                retries += 1

    def _update_stream(self, header: HeaderRDT):
        self.ack_num = header.seq_num + 1
        self.seq_num += header.data_size
        # añadir checks


# Cliente -> ACK: 0,            SQN: 999 ,     DATA: ""
# Server  -> ACK: 999   -1,     SQN: 2011,     DATA: ""
# Cliente -> ACK: 2011 - 1,     SQN: 999 ,     DATA: ""

# Server  -> ACK: 999  - 1,     SQN: 2011,      DATA: "a"
# Cliente -> ACK: 2011 - 1,     SQN: 999  + 1,  DATA: "b"
# Server  -> ACK: 1000 - 1,     SQN: 2011 + 1,  DATA: "a"
# Cliente -> ACK: 2011 - 1,     SQN: 999  + 1,  DATA: "b"
# Server  -> ACK: 1000 - 1,     SQN: 2011 + 1,  DATA: "a"
# Cliente -> ACK: 2011 - 1,     SQN: 999  + 1,  DATA: "b"
