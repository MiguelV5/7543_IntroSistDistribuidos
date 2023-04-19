import socket
import logging

from lib.protocols.stop_and_wait import StopAndWait


class ClientRDT:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = None
        self.protocol = None
        self.protocolArgs = {}

    def connect(self, protocol=StopAndWait, protocolArgs={}):
        logging.info("Client RDT running")
        # create a socket with udp protocol
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        logging.info("Client connecting to: {}:{}".format(
            str(self.host), str(self.port)))

        # try to connect to the server if not return exception
        try:
            sock.connect((self.host, self.port))
        except Exception as e:
            logging.error("Error: " + str(e))
            # create new exception
            raise Exception("Error connecting to server: {}:{}".format(
                str(self.host), str(self.port)))

        logging.info("Client connected to: {}:{}".format(
            str(self.host), str(self.port)))
        self.sock = sock

        # set protocol args
        self.protocolArgs["socket"] = self.sock
        self.protocolArgs["addr"] = (self.host, self.port)
        self.protocolArgs["timeout"] = 5

        # set protocol
        self.protocol = protocol(**self.protocolArgs, debug=True)

    def send(self, data):
        if self.sock is None:
            clientNotConnectedError = "Client not connected to server"
            logging.error(clientNotConnectedError)
            raise Exception(clientNotConnectedError)

        self.protocol.send(data)
