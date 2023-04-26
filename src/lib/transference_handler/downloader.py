
import logging
from lib.utils.constant import SelectedTransferType
from lib.utils.file_handling import FileHandler
from lib.segment_encoding.application_header import ApplicationHeaderRDT


class Downloader():
    def __init__(self, stream,  file_handler: FileHandler):
        self.stream = stream
        self.file_handler = file_handler

    def transfer_type(self):
        return SelectedTransferType.DOWNLOAD

    def run(self, initial_data):
        logging.info("[DOWNLOADER] Decoding application header")
        app_header_bytes = initial_data[:ApplicationHeaderRDT.size()]
        app_header = ApplicationHeaderRDT.from_bytes(app_header_bytes)

        logging.info("[DOWNLOADER] Checking file existence")
        if app_header.file_name != self.file_handler.get_file_name() or app_header.file_size == 0:
            raise ValueError(
                f"[DOWNLOADER] Requested file does not exist: {app_header.file_name}"
            )

        logging.info("[DOWNLOADER] Reading file data by chunks")
        data = initial_data[ApplicationHeaderRDT.size():]
        data_size = len(data)

        while data_size < app_header.file_size:
            if (data_size >= self.file_handler.MAX_RW_SIZE):
                self.file_handler.write(data[:self.file_handler.MAX_RW_SIZE])
                data = data[self.file_handler.MAX_RW_SIZE:]
            new_data = self.stream.read()
            if (new_data is not None) and (new_data != b''):
                data = data + new_data
                data_size += len(new_data)
        if (data is not None and len(data) != 0):
            self.file_handler.write(data)

        logging.info("[DOWNLOADER] Download finished, closing connection")
