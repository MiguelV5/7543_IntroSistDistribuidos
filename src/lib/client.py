import logging
import os
from lib.constant import SelectedProtocol, SelectedTransferType
from lib.sockets_rdt.application_header import ApplicationHeaderRDT

# from lib.protocols.stop_and_wait import StopAndWait
from lib.sockets_rdt.stream_rdt import StreamRDT
from crc import Calculator, Crc8
calculator = Calculator(Crc8.CCITT, optimized=True)


# class ClientRDT:
#     def __init__(self, host, port):
#         self.host = host
#         self.port = port
#         self.stream = None
# self.protocol = None
# self.protocolArgs = {}

# def connect(self, protocol=StopAndWait, protocolArgs={}):
#     logging.info("Client RDT running")
#     # create a socket with udp protocol
#     sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     logging.info("Client connecting to: {}:{}".format(
#         str(self.host), str(self.port)))

#     # try to connect to the server if not return exception
#     try:
#         sock.connect((self.host, self.port))
#     except Exception as e:
#         logging.error("Error: " + str(e))
#         # create new exception
#         raise Exception("Error connecting to server: {}:{}".format(
#             str(self.host), str(self.port)))

#     logging.info("Client connected to: {}:{}".format(
#         str(self.host), str(self.port)))
#     self.stream = sock

#     # set protocol args
#     self.protocolArgs["socket"] = self.stream
#     self.protocolArgs["addr"] = (self.host, self.port)
#     self.protocolArgs["timeout"] = 5

#     # set protocol
#     self.protocol = protocol(**self.protocolArgs, debug=True)

# def send(self, data):
#     if self.stream is None:
#         clientNotConnectedError = "Client not connected to server"
#         logging.error(clientNotConnectedError)
#         raise Exception(clientNotConnectedError)

#     self.protocol.send(data)

class ClientRDT:
    def __init__(self, external_host, external_port,
                 protocol=SelectedProtocol.STOP_AND_WAIT):
        self.external_host = external_host
        self.external_port = external_port
        self.protocol = protocol

    def upload(self, file_name):

         # Instance of ApplicationHeaderRDT - file name and size
        file_size = file_name.size() #os.path.getsize(file_name)
        transfer_type = SelectedTransferType.BINARY
        app_header = ApplicationHeaderRDT(transfer_type, file_name, file_size)

        # Header checksum
        header_checksum = calculator.checksum(app_header.as_bytes())

        # Checksum added to the ApplicationHeaderRDT object
        app_header.header_checksum = header_checksum

        # Connect and do the three way handshake
        stream = StreamRDT.connect(
            self.protocol,  self.external_host, self.external_port,
        )
        logging.info("Client connected to: {}:{}".format(
            stream.external_host, stream.external_port))

        # en este lado hay que enviar los datos del archivo con su nombre
        # aca hay que crear el header de aplicacion con ApplicationHeaderRDT
        # calcular el checksum crc y agregarlo al header
        # Send the header and then the file data
        stream.send(app_header.as_bytes())
        with open(file_name, "rb") as f:
            while True:
                data = f.read(StreamRDT.CHUNK_SIZE)
                if not data:
                    break
                stream.send(data)    

        stream.close()

        # except Exception as e:
        #     logging.error("Error: " + str(e))
        #     exit(1)
