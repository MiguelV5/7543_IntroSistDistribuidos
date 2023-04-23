import logging
import os
from lib.constant import SelectedProtocol, SelectedTransferType
from lib.file_handling import FileHandler, FileHandlerError
from lib.segment_encoding.segment_rdt import SegmentRDT
from lib.sockets_rdt.application_header import ApplicationHeaderRDT
from lib.sockets_rdt.stream_rdt import StreamRDT
from crc import Calculator, Crc8

calculator = Calculator(Crc8.CCITT, optimized=True)


class ClientRDT:
    def __init__(self, external_host, external_port,
                 protocol=SelectedProtocol.STOP_AND_WAIT):
        self.external_host = external_host
        self.external_port = external_port
        self.protocol = protocol

    def upload(self, file_name, file_src_path):

        file_size = os.path.getsize(file_src_path)
        logging.info(
            f"Client RDT starting uploading file: {file_name} of size: {file_size} bytes"  # noqa E501
        )
        transfer_type = SelectedTransferType.UPLOAD

        # Connect and do the three way handshake
        try:
            stream = StreamRDT.connect(
                self.protocol,  self.external_host, self.external_port,
            )
        except (Exception, TimeoutError) as e:
            logging.error("Error trying to connect to the server: " + str(e))
            exit(1)

        logging.info("Client connected to: {}:{}".format(
            stream.external_host, stream.external_port))

        file = FileHandler(file_src_path, "rb")

        chunk_size = SegmentRDT.get_max_segment_size()

        for i in range(0, file_size, chunk_size):
            logging.debug("Sending chunk: " + str(i))
            try:
                data = file.read(chunk_size)
            except FileHandlerError as e:
                logging.error("Error reading file: " + str(e))
                stream.close()
                file.close()
                exit(1)

            if i == 0:
                app_header = ApplicationHeaderRDT(
                    transfer_type, file_name, file_size
                )
                logging.debug(f"Sending application header: {app_header}")
                data = app_header.as_bytes() + data

            stream.send(data)

        file.close()
        stream.close()
