import logging
import os
from threading import Thread
from lib.constant import DEFAULT_SV_STORAGE, DEFAULT_SOCKET_READ_TIMEOUT, SelectedProtocol, SelectedTransferType
from lib.exceptions import ExternalConnectionClosed
from lib.file_handling import FileHandler
from lib.segment_encoding.application_header import ApplicationHeaderRDT

from lib.sockets_rdt.listener_rdt import AccepterRDT, ListenerRDT


class ServerRDT:

    MAX_FILE_SIZE_ALLOWED = 500*1024*1024  # 500 MB
    NO_SUCH_FILE = "No such file"

    def __init__(self, host, port, protocol=SelectedProtocol.STOP_AND_WAIT):
        self.host = host
        self.port = port
        self.protocol = protocol
        self.client_threads = []

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

            client_thread = Thread(target=self.individual_connection_handler,
                                   args=(accepter,))
            self.client_threads.append(client_thread)
            logging.debug(">>>>>>>>>>>>>> NEW THREAD CREATED <<<<<<<<<<<<<<<<")
            client_thread.start()

            for thread in self.client_threads:
                if not thread.is_alive():
                    self.client_threads.remove(thread)

        logging.debug("joining threads")
        for thread in self.client_threads:
            thread.join()

    def individual_connection_handler(
            self, accepter: AccepterRDT
    ):
        try:
            stream = accepter.accept()
        except Exception as e:
            logging.error("Error accepting connection: " + str(e))
            return

        try:
            initial_data = stream.read()
            app_header_bytes = initial_data[:ApplicationHeaderRDT.size()]
            app_header = ApplicationHeaderRDT.from_bytes(app_header_bytes)
        except Exception as e:
            logging.error("Error reading application header: " + str(e))
            stream.close()
            return

        file_name = app_header.file_name
        transfer_type = app_header.transfer_type

        logging.info("Received application header: {}".format(str(app_header)))

        try:
            self.handle_transfer_by_type(stream, transfer_type,
                                         file_name, initial_data, app_header)
        except Exception as e:
            logging.error("Error handling transference: " + str(e))
            stream.close()
            return

    def handle_transfer_by_type(self, stream, transfer_type, file_name, initial_data, app_header):
        if transfer_type == SelectedTransferType.UPLOAD:
            if len(initial_data) > ApplicationHeaderRDT.size():
                start_of_user_data = initial_data[ApplicationHeaderRDT.size():]
            else:
                start_of_user_data = b""
            remaining_file_size = app_header.file_size - \
                len(start_of_user_data)
            self.handle_upload_request(
                stream, file_name, remaining_file_size, start_of_user_data
            )
        elif transfer_type == SelectedTransferType.DOWNLOAD:
            self.handle_download_request(stream, file_name)

    def handle_download_request(self, stream, file_name):

        file_path = DEFAULT_SV_STORAGE + file_name

        if FileHandler.file_exists(file_path) is False:
            logging.info(
                f"The file: {file_name}  requested to download from client: ({stream.external_host}:{stream.external_port}) doesn't exists"
            )
            app_header = ApplicationHeaderRDT(
                self.NO_SUCH_FILE, SelectedTransferType.DOWNLOAD, 0)
            try:
                stream.send(app_header.as_bytes())
            except Exception:
                pass
            stream.close()
            return

        file = FileHandler(file_path, "rb")

        app_header = ApplicationHeaderRDT(
            SelectedTransferType.DOWNLOAD, file_name, file.size())
        try:
            print(">>>>>>> sending app header: {}".format(str(app_header)))
            stream.send(app_header.as_bytes())
            logging.info(
                f"Successfully sent application header of file: {file_name} to client: ({stream.external_host}:{stream.external_port})")
        except Exception as e:
            print(">>>>>>> error sending app header: {}".format(str(e)))
            file.close()
            stream.close()
            return

        chunk_size = FileHandler.MAX_READ_SIZE

        file_size = file.size()

        for _ in range(0, file_size, chunk_size):
            try:
                data = file.read(chunk_size)
                stream.send(data)
            except Exception:
                stream.close()
                file.close()
                return

        file.close()
        logging.info(f"Successfully sent file: {file_name}")

        stream.close()

    def handle_upload_request(self, stream, file_name, remaining_file_size, start_of_user_data):
        file_path = DEFAULT_SV_STORAGE + file_name
        file = FileHandler(file_path, "wb")

        if file.size() > self.MAX_FILE_SIZE_ALLOWED:
            logging.error(
                f"The file: {file_name}  requested to upload from client: ({stream.external_host}:{stream.external_port}) exceeds the maximum file size allowed"
            )
            file.close()
            return

        try:
            if (len(start_of_user_data) > 0):
                file.write(start_of_user_data)
        except Exception as e:
            file.close()
            raise e

        while remaining_file_size > 0:
            try:
                new_data = stream.read()
                file.write(new_data)
                remaining_file_size -= len(new_data)
            except ExternalConnectionClosed:
                break
            except Exception as e:
                file.close()
                raise e

        # if remaining_file_size > 0:
        #     logging.error(
        #         f"Client: ({stream.external_host}:{stream.external_port}) closed the connection before sending the entire file"
        #     )
        #     file.close()
        #     # delete the written file with the os library
        #     os.remove(file_path)
        #     stream.close()
        #     return

        file.close()
        logging.info(f"Successfully received file: {file_name}")
