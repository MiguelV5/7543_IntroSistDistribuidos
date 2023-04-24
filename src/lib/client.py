import logging
import os
from lib.constant import DEFAULT_SOCKET_RECV_TIMEOUT, SelectedProtocol, SelectedTransferType
from lib.exceptions import ExternalConnectionClosed
from lib.file_handling import FileHandler
from lib.segment_encoding.application_header import ApplicationHeaderRDT
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
            f"[UPLOAD] Client RDT starting uploading file: {file_name} of size: {file_size} bytes"
        )
        transfer_type = SelectedTransferType.UPLOAD

        # Connect and do the three way handshake
        try:
            stream = StreamRDT.connect(
                self.protocol,  self.external_host, self.external_port,
            )
        except (Exception, TimeoutError) as e:
            logging.error("Error trying to connect to the server: " + str(e))
            raise e

        logging.info("[UPLOAD] Client connected to: {}:{}".format(
            stream.external_host, stream.external_port))

        stream.settimeout(DEFAULT_SOCKET_RECV_TIMEOUT)

        file = FileHandler(file_src_path, "rb")
        app_header = ApplicationHeaderRDT(
            transfer_type, file_name, file_size
        )
        data = app_header.as_bytes()

        try:
            stream.send(data)
        except TimeoutError as e:
            stream.close()
            file.close()
            raise e

        chunk_size = FileHandler.MAX_READ_SIZE

        for _ in range(0, file_size, chunk_size):
            try:
                data = file.read(chunk_size)
                stream.send(data)
            except Exception as e:
                stream.close()
                file.close()
                raise e

        file.close()
        stream.close()

    def download(self, file_name, file_dst_path):

        logging.info(
            f"[DOWNLOAD] Client RDT starting download of file: {file_name}"
        )
        transfer_type = SelectedTransferType.DOWNLOAD

        # Connect and do the three way handshake
        try:
            stream = StreamRDT.connect(
                self.protocol, self.external_host, self.external_port,
            )
        except (Exception, TimeoutError) as e:
            logging.error(
                "Error trying to connect to the server: " + str(e))
            raise e

        logging.info("[DOWNLOAD] Client connected to: {}:{}".format(
            stream.external_host, stream.external_port))

        stream.settimeout(DEFAULT_SOCKET_RECV_TIMEOUT)

        file = FileHandler(file_dst_path, "wb")

        # Send the application header
        app_header = ApplicationHeaderRDT(
            transfer_type, file_name, 0
        )
        data = app_header.as_bytes()

        try:
            stream.send(data)
        except TimeoutError as e:
            stream.close()
            file.close()
            raise e

        # Receive the application header containing the file size
        try:
            initial_data = stream.read()
            app_header_bytes = initial_data[:ApplicationHeaderRDT.size()]
            app_header = ApplicationHeaderRDT.from_bytes(app_header_bytes)
            if app_header.file_size > ApplicationHeaderRDT.size():
                start_of_server_data = initial_data[ApplicationHeaderRDT.size(
                ):]
                remaining_file_size = app_header.file_size - \
                    len(start_of_server_data)
            else:
                start_of_server_data = b""
                remaining_file_size = app_header.file_size
        except ExternalConnectionClosed:
            logging.error(
                f"Server: ({stream.external_host}:{stream.external_port}) closed the connection before sending the entire file"
            )
            file.close()
            os.remove(file_dst_path)
            stream.close()
            return
        except Exception as e:
            logging.error("Error reading application header: " + str(e))
            stream.close()
            return

        # NOTE Como convencion, para determinar que el archivo no existe en el server
        if app_header.file_name != file_name or app_header.file_size == 0:
            logging.error(
                f"Server doesn't have the requested file: {app_header.file_name}"
            )
            file.close()
            stream.close()
            return

        logging.info("Received application header: {}".format(str(app_header)))

        try:
            file.write(start_of_server_data)
        except Exception as e:
            file.close()
            stream.close()
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
                stream.close()
                raise e

        if remaining_file_size > 0:
            logging.error(
                f"Server: ({stream.external_host}:{stream.external_port}) closed the connection before sending the entire file"
            )
            file.close()
            os.remove(file_dst_path)
            stream.close()
            return

        file.close()
        stream.close()
