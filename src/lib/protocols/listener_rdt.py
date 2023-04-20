

import random
import logging
import socket
from lib.protocols.stream_rdt import StreamRDT
from lib.segment_handler.header_rdt import HeaderRDT
from lib.segment_handler.segment_rdt import SegmentRDT


class ListenerRDT():

    def __init__(self, sv_host,  sv_port):

        self.sv_host = sv_host
        self.sv_port = sv_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('', self.sv_port))

    def listen(self):
        while True:
            data, addr = self.socket.recvfrom(HeaderRDT.size())

            try:
                segment = SegmentRDT.from_bytes(data)
                # check header
                break
            except ValueError:
                logging.debug("Invalid segment received")

        stream = StreamRDT(self.sv_host, self.sv_port,
                           addr[0], addr[1], random.randint(0, 2**31),
                           segment.header.sqn
                           )
        stream.send_handshake()
        #recibir un handshake
        #devolver un StreamRDT
        # stream.send()
