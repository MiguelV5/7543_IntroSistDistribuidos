import logging
from threading import Thread
from lib.utils.constant import DEFAULT_SV_STORAGE, SelectedProtocol, SelectedTransferType
from lib.transference_handler.downloader import Downloader
from lib.utils.file_handling import FileHandler
from lib.segment_encoding.application_header import ApplicationHeaderRDT

from lib.sockets_rdt.listener_rdt import AccepterRDT, ListenerRDT
from lib.transference_handler.uploader import Uploader


class ServerRDT:

    MAX_FILE_SIZE_ALLOWED = 500*1024*1024  # 500 MB
    NO_SUCH_FILE = "No such file"

    def __init__(self, host, port, protocol=SelectedProtocol.STOP_AND_WAIT):
        self.host = host
        self.port = port
        self.protocol = protocol
        self.server_ports_threads = []

    def run(self):

        listener = ListenerRDT(self.host, self.port, self.protocol)

        while True:
            try:
                accepter = listener.listen()
            except KeyboardInterrupt:
                logging.debug("Keyboard interrupt received. Exiting...")
                break
            except Exception as e:
                logging.error("Error listening: " + str(e))
                continue

            client_thread = Thread(target=self.server_port_handler,
                                   args=(accepter,))
            self.server_ports_threads.append(client_thread)
            client_thread.start()

            for thread in self.server_ports_threads:
                if not thread.is_alive():
                    self.server_ports_threads.remove(thread)

        for thread in self.server_ports_threads:
            thread.join()

    def server_port_handler(
            self, accepter: AccepterRDT
    ):
        try:
            stream = accepter.accept()

            initial_data = stream.read()

            app_header_bytes = initial_data[:ApplicationHeaderRDT.size()]
            app_header = ApplicationHeaderRDT.from_bytes(app_header_bytes)
        except Exception as e:
            logging.error(
                "[PORT HANDLER] Error starting connection: " + str(e))
            return

        try:
            self.handle_transference(stream, app_header, initial_data)
        except Exception as e:
            logging.error(
                "[PORT HANDLER] Error handling transference: " + str(e))
            stream.close()
            return

    def handle_transference(self, stream, app_header: ApplicationHeaderRDT, initial_data: bytes):
        file_name = app_header.file_name
        transfer_type = app_header.transfer_type

        if transfer_type == SelectedTransferType.UPLOAD:
            self.download(
                stream, file_name, initial_data
            )
        elif transfer_type == SelectedTransferType.DOWNLOAD:
            self.upload(stream, file_name)

    def upload(self, stream, file_name):
        file_handler = FileHandler(
            DEFAULT_SV_STORAGE + file_name, file_name, "rb")

        if FileHandler.file_exists(file_handler.get_file_path()) is False:
            app_header = ApplicationHeaderRDT(
                self.NO_SUCH_FILE, SelectedTransferType.DOWNLOAD, 0)
            stream.send(app_header.as_bytes())
            logging.info(
                f"[SERVER UPLOAD] Sending App Header, file does not exist: {app_header}")
            return

        uploader = Uploader(stream, file_handler)
        uploader.run()

    def download(self, stream, file_name, start_of_user_data):
        file = FileHandler(DEFAULT_SV_STORAGE + file_name, file_name, "wb")

        downloader = Downloader(stream, file)
        downloader.run(start_of_user_data)
