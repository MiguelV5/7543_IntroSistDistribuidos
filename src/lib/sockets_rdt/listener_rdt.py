

import logging
import socket
from lib.constant import Protocol
from lib.sockets_rdt.handshake_header import HandshakeHeaderRDT

from lib.segment_encoding.header_rdt import HeaderRDT
from lib.segment_encoding.segment_rdt import SegmentRDT
from lib.sockets_rdt.stream_rdt import StreamRDT


class ListenerRDT():

    def __init__(self, host,  port):

        self.host = host
        self.port = port
        self.client_counter = 0
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('', self.port))
        self.socket.settimeout(5)

    def _check_first_header(self, header):
        if header.data_size != HandshakeHeaderRDT.size():
            raise Exception("Invalid data size")
        if header.ack != 0:
            raise Exception("Invalid ack number")
        if not header.syn:
            raise Exception("Invalid syn number")
        if header.fin:
            raise Exception("Invalid fin")

    def listen(self):
        # TODO Logica de intentos

        while True:
            try:
                data, external_address = self.socket.recvfrom(HeaderRDT.size())
                segment = SegmentRDT.from_bytes(data)
                self._check_first_header(segment.header)
                self.client_counter += 1
                break
            except TimeoutError:
                continue
            except Exception as e:
                logging.debug("Invalid segment received: {}".format(e))
                continue

        stream = StreamRDT.from_listener(
            Protocol.STOP_AND_WAIT,
            external_address[0], external_address[1],
            self.host, self.port + self.client_counter,
            segment
        )

        return stream
