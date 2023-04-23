import logging
from threading import Thread
from lib.constant import SelectedProtocol

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

        # protocol.read()
        data = stream.read()
        # cuando termine de leer se llama al stream close
        logging.info("Received data: {}".format(str(data)))
        stream.close()
