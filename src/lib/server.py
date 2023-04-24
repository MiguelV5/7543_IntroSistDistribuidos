import logging
from threading import Thread
from lib.constant import SelectedProtocol
from lib.file_handling import FileHandler
from lib.sockets_rdt.application_header import ApplicationHeaderRDT

from lib.sockets_rdt.listener_rdt import AccepterRDT, ListenerRDT


class ServerRDT:
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
            client_thread.start()

            for thread in self.client_threads:
                if not thread.is_alive():
                    self.client_threads.remove(thread)
                thread.join()

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
            exit(1)

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
