

import logging
import socket
from lib.constant import SelectedProtocol
from lib.sockets_rdt.handshake_header import HandshakeHeaderRDT

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
        if header.data_size != HandshakeHeaderRDT.size():
            raise Exception("Invalid data size")
        if header.ack_num != StreamRDT.START_ACK:
            raise Exception("Invalid ack number")
        if not header.syn:
            raise Exception("Invalid syn number")
        if header.fin:
            raise Exception("Invalid fin")

    def listen(self):
        # TODO Logica de intentos

        while True:
            try:
                logging.info("Waiting for incoming connection")
                data, external_address = self.socket.recvfrom(
                    HeaderRDT.size() + HandshakeHeaderRDT.size())
                segment = SegmentRDT.from_bytes(data)
                self._check_first_header(segment.header)
                self.client_counter += 1
                break
            except TimeoutError:
                continue
            except Exception as e:
                logging.error("Invalid segment received: {}".format(e))
                continue

        logging.info("Coonection attempt from {}".format(external_address))

        # NOTE (Miguel): Añadido otro valor de retorno para tener la info
        #  correcta ya verificada del pedido del cliente tras el handshake.
        #  Misma nota en stream_rdt.py:143
        # NOTE 2: de paso ya arregle un monton de problemas relacionados a bytes.
        # Ahora hay que ver por que esta fallando el handshake en el cliente
        # Tira como que siempre esta recibiendo el handshake header
        stream, successful_handshake_header = StreamRDT.from_listener(
            SelectedProtocol.STOP_AND_WAIT,
            external_address[0], external_address[1],
            segment, self.host, self.port + self.client_counter
        )

        logging.info("Connection established with {}".format(external_address))

        return stream, successful_handshake_header
