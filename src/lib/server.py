import socket
import logging


class ServerRDT:

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def create(self):
        logging.info("Server RDT running")
        # create a socket with udp protocol
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # bind the socket to the port
        sock.bind((self.host, self.port))
        logging.info("Server running on port: {}".format(str(self.port)))

        # listen for incoming messages
        while True:
            data, addr = sock.recvfrom(1024)
            logging.info("New Message from: {}".format(str(addr)))
            logging.info("Message: {} received".format(data.decode("utf-8")))
            sock.sendto(data, addr)
