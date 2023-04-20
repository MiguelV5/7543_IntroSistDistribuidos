

import random
import logging
import socket
from lib.sockets_rdt.stream_rdt import StreamRDT
from lib.segment_encoding.header_rdt import HeaderRDT
from lib.segment_encoding.segment_rdt import SegmentRDT


class ListenerRDT():

    def __init__(self, sv_host,  sv_port):

        self.sv_host = sv_host
        self.sv_port = sv_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('', self.sv_port))
        self.socket.settimeout(5)

    def listen(self):
        while True:
            try:
                data, addr = self.socket.recvfrom(HeaderRDT.size())
            except TimeoutError:
                continue

            try:
                segment = SegmentRDT.from_bytes(data)
                # check header
                break
            except Exception as e:
                logging.debug("Invalid segment received: {}".format(e))
                continue

        stream = StreamRDT(self.sv_host, self.sv_port,
                           addr[0], addr[1], random.randint(0, 2**31),
                           segment.header.sqn
                           )
        stream.run_handshake_as_server()

        # devolver un StreamRDT
        # stream.send()
