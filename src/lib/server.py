import socket
import logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ServerRDT")

class ServerRDT:
    
        def __init__(self, host, port):
            self.host = host
            self.port = port
    
        def create(self):
            logger.info("Server RDT running")
            # create a socket with udp protocol
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # bind the socket to the port
            sock.bind((self.host, self.port))
            logger.info("Server running on port: {}".format(str(self.port)))

            # listen for incoming messages
            while True:
                data, addr = sock.recvfrom(1024)
                logger.info("New Message from: {}".fprmat(str(addr)))
                logger.info("Message: {} received".format(data.decode("utf-8")))
                sock.sendto(data, addr)