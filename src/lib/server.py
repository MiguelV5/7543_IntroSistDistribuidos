import socket
import logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ServerRDT")

class ServerRDT:
    
        def __init__(self, args):
            self.args = args
    
        def create(self):
            logger.info("Server RDT running")
            # create a socket with udp protocol
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # bind the socket to the port
            sock.bind((self.args.host, self.args.port))
            logger.info("Server running on port: " + str(self.args.port))
            # listen for incoming messages
            while True:
                data, addr = sock.recvfrom(1024)
                logger.info("New Message from: " + str(addr))
                logger.info("Message: " + data.decode("utf-8") + " received")
                sock.sendto(data, addr)