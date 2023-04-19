import socket
import logging

from lib.protocols.stop_and_wait import StopAndWait


class ServerRDT:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.protocol = None
        self.protocolArgs = {}
        self.mss = 1024
        self.header = {}
        self.header["sqn"] = 0
        self.header["ack"] = 0

    def create(self, protocol=StopAndWait, protocolArgs={}):
        logging.info("Server RDT running")
        # create a socket with udp protocol
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # bind the socket to the port
        sock.bind((self.host, self.port))
        logging.info("Server running on port: {}".format(str(self.port)))

        # set protocol args
        self.protocolArgs["addr"] = (self.host, self.port)
        self.protocolArgs["socket"] = sock
        # set protocol
        self.protocol = protocol(**self.protocolArgs)

        # listen for incoming messages
        while True:
            packet, addr = sock.recvfrom(self.mss + len(self.header))
            logging.info("from: {}".format(addr))
            logging.info(
                "Received data from: {} data: {}".format(addr, str(packet)))

            # TODO: possible solution of concurrent connections?
            # dictionary of keys with address value threads
            # dictionary of keys with address and channels of threads

            data = self.protocol.receive(packet, addr)
            if len(data) > 0:
                logging.info("Received data lenght: {}".format(len(data)))
            # TODO: concat the data received from the client to make the file
