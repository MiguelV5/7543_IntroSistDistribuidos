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
        logging.info("[SERVER] Starting server")
        listener = ListenerRDT(self.host, self.port, self.protocol)

        logging.info("[SERVER] Listening for connections")
        while True:
            try:
                accepter = listener.listen()
            except KeyboardInterrupt:
                logging.debug(
                    "[SERVER] Keyboard interrupt received, closing server")
                break
            except Exception as e:
                logging.error("[SERVER] Error listening: " + str(e))
                continue

            client_thread = Thread(target=self.server_port_handler,
                                   args=(accepter,))
            self.server_ports_threads.append(client_thread)
            client_thread.start()

            for thread in self.server_ports_threads:
                if not thread.is_alive():
                    logging.info("[SERVER] Removing dead thread")
                    self.server_ports_threads.remove(thread)

        logging.info("[SERVER] Waiting for threads to finish")
        for thread in self.server_ports_threads:
            thread.join()
        logging.info("[SERVER] ALl threads finished")

    def server_port_handler(
            self, accepter: AccepterRDT
    ):
        try:
            logging.info(
                f"[PORT HANDLER] Accepting connection from client {accepter.external_host}:{accepter.external_port}")
            stream = accepter.accept()

            initial_data = stream.read()

            app_header_bytes = initial_data[:ApplicationHeaderRDT.size()]
            app_header = ApplicationHeaderRDT.from_bytes(app_header_bytes)
            logging.info(
                f"[PORT HANDLER] Reading Applicaton Header: {app_header}")
        except Exception as e:
            logging.error(
                "[PORT HANDLER] Error starting connection: " + str(e))
            return

        self.handle_transference(stream, app_header, initial_data)

    def handle_transference(self, stream, app_header: ApplicationHeaderRDT, initial_data: bytes):
        file_name = app_header.file_name
        transfer_type = app_header.transfer_type
        file_handler = None
        try:
            if transfer_type == SelectedTransferType.UPLOAD:
                logging.info(
                    "[PORT HANDLER] Transference type: UPLOAD")
                logging.info("[PORT HANDLER] Opening file to download")
                file_handler = FileHandler(
                    DEFAULT_SV_STORAGE + file_name, file_name, "wb")
                self.download(
                    stream, file_handler, initial_data
                )
            elif transfer_type == SelectedTransferType.DOWNLOAD:
                logging.info(
                    "[PORT HANDLER] Transference type: DOWNLOAD")
                logging.info(
                    "[PORT HANDLER] Checking file existence")
                self._check_if_file_exist(file_name, stream)

                logging.info(
                    "[PORT HANDLER] Checking file existence")

                logging.info("[PORT HANDLER] Opening file to upload")
                file_handler = FileHandler(
                    DEFAULT_SV_STORAGE + file_name, file_name, "rb")
                self.upload(stream, file_handler)
        except Exception as e:
            logging.error(
                "[PORT HANDLER] Error handling transference: " + str(e))
        finally:
            if (file_handler):
                file_handler.close()
            if (stream):
                stream.close()

    def upload(self, stream, file_handler):
        uploader = Uploader(stream, file_handler)
        uploader.run()

    def download(self, stream, file_handler, start_of_user_data):
        downloader = Downloader(stream, file_handler)
        downloader.run(start_of_user_data)

    def _check_if_file_exist(self, file_name, stream):
        if FileHandler.file_exists(DEFAULT_SV_STORAGE + file_name):
            return

        app_header = ApplicationHeaderRDT(
            SelectedTransferType.DOWNLOAD, self.NO_SUCH_FILE, 0)
        stream.send(app_header.as_bytes())

        logging.error(
            f"[SERVER UPLOAD] Sending App Header, file does not exist: {app_header}")
        raise ValueError("[SERVER UPLOAD] File doesn't exists")
