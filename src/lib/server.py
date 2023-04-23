import logging
from threading import Thread
from lib.constant import SelectedProtocol
from lib.file_handling import FileHandler
from lib.sockets_rdt.application_header import ApplicationHeaderRDT

from lib.sockets_rdt.listener_rdt import ListenerRDT
from lib.sockets_rdt.stream_rdt import StreamRDT


class ServerRDT:
    def __init__(self, host, port, protocol=SelectedProtocol.STOP_AND_WAIT):
        self.host = host
        self.port = port
        self.protocol = protocol
        self.client_threads = []

    def run(self):

        listener = ListenerRDT(self.host, self.port, self.protocol)

        while True:
            stream = listener.listen()

            client_thread = Thread(target=self.thread_function,
                                   args=(stream,))
            self.client_threads.append(client_thread)
            client_thread.start()

            for thread in self.client_threads:
                if not thread.is_alive():
                    self.client_threads.remove(thread)
                thread.join()

    def thread_function(
            self, stream: StreamRDT
    ):
        # aca hay que ir leyendo con read hasta que complete el archivo
        # como completamos el archivo? porque el header tiene el size
        # como se obtiene el size se lee del primer paquete el header de aplicacion

        data = stream.read()

        try:
            app_header_bytes = data[:ApplicationHeaderRDT.size()]

            app_header = ApplicationHeaderRDT.from_bytes(app_header_bytes)
            data = data[ApplicationHeaderRDT.size():]
        except Exception as e:
            logging.error("Error reading application header: " + str(e))
            stream.close()
            exit(1)

        remaining_file_size = app_header.file_size - len(data)
        file_name = app_header.file_name
        transfer_type = app_header.transfer_type

        logging.info("Received application header: {}".format(str(app_header)))
        logging.info("Received file name: {}".format(file_name))
        logging.info("Received transfer type: {}".format(transfer_type))

        while remaining_file_size > 0:
            new_data = stream.read()
            data += new_data
            remaining_file_size -= len(new_data)

        file_path = "./sv_storage/" + file_name
        file = FileHandler(file_path, "wb")
        file.write(data)

        file.close()
        stream.close()
