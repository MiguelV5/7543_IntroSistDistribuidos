
import logging
from lib.constant import SelectedTransferType
from lib.file_handling import FileHandler
from lib.segment_encoding.application_header import ApplicationHeaderRDT


class Downloader():
    def __init__(self, stream,  file_handler: FileHandler):
        self.stream = stream
        self.file_handler = file_handler

    def transfer_type(self):
        return SelectedTransferType.DOWNLOAD

    def run(self, initial_data):

        app_header_bytes = initial_data[:ApplicationHeaderRDT.size()]
        app_header = ApplicationHeaderRDT.from_bytes(app_header_bytes)

        if app_header.file_name != self.file_handler.get_file_name() or app_header.file_size == 0:
            raise ValueError(
                f"[DOWNLOADER] Requesested file does not exist: {app_header.file_name}"
            )

        data = initial_data[ApplicationHeaderRDT.size():]
        data_size = len(data)

        while data_size < app_header.file_size:
            if (data == self.file_handler.MAX_RW_SIZE):
                self.file_handler.write(data)
                data = b""
            new_data = self.stream.read()
            data = data + new_data
            data_size += len(new_data)
