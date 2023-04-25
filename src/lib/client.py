import logging
from lib.utils.constant import SelectedProtocol, SelectedTransferType
from lib.transference_handler.downloader import Downloader
from lib.utils.file_handling import FileHandler
from lib.segment_encoding.application_header import ApplicationHeaderRDT
from lib.sockets_rdt.stream_rdt import StreamRDT
from crc import Calculator, Crc8

from lib.transference_handler.uploader import Uploader

calculator = Calculator(Crc8.CCITT, optimized=True)


class ClientRDT:

    def __init__(self, external_host, external_port,
                 protocol=SelectedProtocol.STOP_AND_WAIT):
        self.external_host = external_host
        self.external_port = external_port
        self.protocol = protocol

    def upload(self, file_path, file_name):
        try:
            file_handler = FileHandler(file_path, file_name, "rb")

            stream = StreamRDT.connect(
                self.protocol, self.external_host, self.external_port,
            )

            uploader = Uploader(stream, file_handler)
            uploader.run()
        except Exception as e:
            logging.error("[CLIENT UPLOAD] Error uploading file: " + str(e))
            exit(1)
        finally:
            if (file_handler):
                file_handler.close()
            if (stream):
                stream.close()

    def download(self, file_path, file_name):
        try:
            file_handler = FileHandler(file_path, file_name, "wb")

            stream = StreamRDT.connect(
                self.protocol, self.external_host, self.external_port,
            )
            app_header = ApplicationHeaderRDT(
                SelectedTransferType.DOWNLOAD, file_handler.get_file_name
                (), 0
            )
            stream.send(app_header.as_bytes())
            logging.info(f"[CLIENT DOWNLOAD] Sending App Header: {app_header}")

            initial_data = stream.read()
            logging.info(f"[CLIENT DOWNLOAD] Receiving Data: {initial_data}")

            downloader = Downloader(stream, file_handler)
            downloader.run(initial_data)
        except Exception as e:
            logging.error(
                "[CLIENT DOWNLOAD] Error downloading file: " + str(e))
        finally:
            if (file_handler):
                file_handler.close()
            if (stream):
                stream.close()
