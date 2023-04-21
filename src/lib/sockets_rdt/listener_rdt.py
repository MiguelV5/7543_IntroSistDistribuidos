

import logging
import socket
from lib.constant import SelectedProtocol
from lib.sockets_rdt.application_header import ApplicationHeaderRDT

from lib.segment_encoding.header_rdt import HeaderRDT
from lib.segment_encoding.segment_rdt import SegmentRDT
from lib.sockets_rdt.stream_rdt import StreamRDT


class ListenerRDT():

    def __init__(self, host, port):

        self.host = host
        self.port = port
        self.client_counter = 0
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('', self.port))
        self.socket.settimeout(5)

    def _check_first_header(self, header: HeaderRDT):
        if header.data_size != ApplicationHeaderRDT.size():
            raise Exception("Invalid data size")
        if header.ack_num != StreamRDT.START_ACK:
            raise Exception("Invalid ack number")
        if not header.syn:
            raise Exception("Invalid syn number")
        if header.fin:
            raise Exception("Invalid fin")

    def listen(self):
        # TODO Logica de intentos
        logging.info("Waiting for incoming connection")
        while True:
            try:
                data, external_address = self.socket.recvfrom(
                    HeaderRDT.size() + ApplicationHeaderRDT.size())
                segment = SegmentRDT.from_bytes(data)
                self._check_first_header(segment.header)
                self.client_counter += 1
                break
            except socket.timeout:
                continue
            except Exception as e:
                logging.error("Invalid segment received: {}".format(e))
                continue

        logging.info("Conection attempt from {}".format(external_address))

        stream, successful_app_header = StreamRDT.from_listener(
            SelectedProtocol.STOP_AND_WAIT,
            external_address[0], external_address[1],
            segment, self.host
        )

        logging.info("Connection established with {}".format(external_address))

        return stream, successful_app_header
