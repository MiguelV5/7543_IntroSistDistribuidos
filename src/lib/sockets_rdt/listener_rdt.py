import logging
import socket
from lib.utils.constant import SelectedProtocol
from lib.segment_encoding.application_header import ApplicationHeaderRDT

from lib.segment_encoding.header_rdt import HeaderRDT
from lib.segment_encoding.segment_rdt import SegmentRDT
from lib.sockets_rdt.stream_rdt import StreamRDT


class ListenerRDT():

    def __init__(self, host, port, protocol=SelectedProtocol.STOP_AND_WAIT):

        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('', self.port))
        self.socket.settimeout(None)  # Desired for the listener
        self.protocol = protocol

    def _check_first_header(self, header: HeaderRDT):
        if header.data_size != 0:
            raise Exception("Invalid data size")
        if header.ack_num != StreamRDT.START_ACK:
            raise Exception("Invalid ack number")
        if not header.syn:
            raise Exception("Invalid syn number")
        if header.fin:
            raise Exception("Invalid fin")

    def listen(self):
        while True:
            logging.info("Listening for incoming connections")
            try:
                data, external_address = self.socket.recvfrom(
                    HeaderRDT.size() + ApplicationHeaderRDT.size())
                segment = SegmentRDT.from_bytes(data)
                self._check_first_header(segment.header)
                break
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except socket.timeout:
                continue
            except (Exception, ValueError) as e:
                logging.error("Invalid segment received: {}".format(e))
                continue

        logging.info(
            "[HANDSHAKE] Conection attempt from {}".format(external_address))
        logging.debug("[HANDSHAKE] LISTENER 1 (read)")

        return AccepterRDT(self, segment, external_address)


class AccepterRDT():

    def __init__(self, listener: ListenerRDT, first_segment, external_address):
        self.host = listener.host
        self.first_segment = first_segment
        self.external_host = external_address[0]
        self.external_port = external_address[1]
        self.protocol = listener.protocol

    def accept(self):

        stream = StreamRDT.from_listener(
            self.protocol,
            self.external_host, self.external_port,
            self.first_segment, self.host
        )

        logging.info("[LISTENER] Connection established with ({}:{})".format(
            self.external_host, self.external_port)
        )

        return stream
