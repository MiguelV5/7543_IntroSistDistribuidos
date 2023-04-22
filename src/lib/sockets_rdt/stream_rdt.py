

import logging
import socket
from lib.sockets_rdt.application_header import ApplicationHeaderRDT
from lib.constant import DEFAULT_TIMEOUT, SelectedTransferType

from lib.segment_encoding.header_rdt import HeaderRDT
from lib.segment_encoding.segment_rdt import SegmentRDT


class StreamRDT():

    START_ACK = 0
    START_LISTENER_SEQ = 1000
    START_CONNECT_SEQ = 2000

    MAX_HANDSHAKE_TIMEOUT_RETRIES = 5
    MAX_READ_TIMEOUT_RETRIES = 3
    MAX_CLOSE_RETRIES = 5

    def __init__(self, protocol, external_host, external_port,
                 seq_num, ack_num, host, port=None):
        # NOTE (Miguel) Añadido ultimo param para poder actualizar el valor
        # del puerto para la creacion del stream con el que se van
        # a comunicar permanentemente con el server a partir del
        # handshake inclusive
        self.protocol = protocol
        self.external_host = external_host
        self.external_port = external_port
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('', 0 if port is None else port))
        self.port = self.socket.getsockname()[1]
        self.socket.settimeout(DEFAULT_TIMEOUT)

        self.seq_num = seq_num
        self.ack_num = ack_num

    @classmethod
    def from_listener(
        cls, protocol, external_host, external_port,
        segment: SegmentRDT, host, port=None
    ):
        stream = cls(
            protocol, external_host, external_port,
            cls.START_LISTENER_SEQ, segment.header.ack_num,
            host, port,
        )

        app_header = ApplicationHeaderRDT.from_bytes(segment.data)
        stream.run_handshake_as_listener(app_header)
        return stream, app_header
        # TODO: Siempre devolver el Transfer Information porquee las
        # capas de arriba no deberian saber lo del handsahke header

    @classmethod
    def connect(
        cls, protocol, external_host,
        external_port, transfer_type
    ):
        stream = cls(
            protocol, external_host, external_port, cls.START_CONNECT_SEQ,
            StreamRDT.START_ACK, 'localhost'
        )
        logging.info("Connecting to {}:{} with my port: {}".format(
            external_host, external_port, stream.port))
        # stream.socket.bind(('localhost', stream.port))
        # TODO Pasarle todo lo que se hardcodea en el HandshakeHeader
        stream.run_handshake_as_initiator(transfer_type)
        return stream

    def settimeout(self, seconds):
        self.socket.settimeout(seconds)

    # ======================== FOR PUBLIC USE ========================

    def send(self, data: bytes):
        self._send_base(data, False, False)

    def read(self) -> bytes:
        segment, external_address = self._read_base()

        self._check_address(
            segment.header, external_address
        )
        self._update_stream(segment.header)
        return segment.data

    def close_external_connection(self):
        logging.debug("Closing external connection")
        retries = 0
        while retries < self.MAX_CLOSE_RETRIES:
            self._send_base(b'', False, True)
            try:
                segment, external_address = self._read_base()
                self._check_address(
                    segment.header, external_address
                )
                if segment.header.fin:
                    logging.debug("External connection closed")
                    break
                else:
                    retries += 1
                    continue
            except (TimeoutError, ValueError):
                retries += 1
                continue

            # TODO: Que pasa si el segmento que recibo no es un fin?
            # Puede que todavia no se haya recibido todo lo de un archivo

    def close(self):
        logging.debug("Closing socket")
        self.close_external_connection()
        self.socket.close()

    def _check_address(
        self, header: HeaderRDT, external_address
    ):
        if external_address[0] != self.external_host:
            raise ValueError("Invalid external host")
        elif external_address[1] != self.external_port:
            raise ValueError("Invalid external_port")

        # TODO posible check de header (syn y fin)
    # TODO  def _check_segment_at_handshake
    # TODO  def _check_segment_at_close

    # ======================== FOR PRIVATE USE ========================

    def _send_base(self, data: bytes, syn, fin):
        logging.debug("Sending data from {}:{} ->  {}:{}".format(
            self.host, self.port, self.external_host, self.external_port))

        header = HeaderRDT(len(data), self.seq_num, self.ack_num, syn, fin)
        segment = SegmentRDT(header, data)

        self.socket.sendto(
            segment.as_bytes(),
            (self.external_host, self.external_port)
        )

    def _read_base(self) -> tuple[SegmentRDT, tuple]:
        retries = 0
        logging.debug("Trying to read data from {}:{} ->  {}:{}".format(
            self.external_host, self.external_port, self.host, self.port))
        while retries < self.MAX_READ_TIMEOUT_RETRIES:
            try:
                segment_as_bytes, external_address = self.socket.recvfrom(
                    SegmentRDT.MAX_SEGMENT_SIZE + HeaderRDT.size())
                segment = SegmentRDT.from_bytes(segment_as_bytes)
                return segment, external_address
            except socket.timeout:
                retries += 1
                logging.debug("Timeout while reading")
                continue
            except ValueError as e:
                retries += 1
                logging.error("Invalid segment received:  " + str(e))
                continue
        raise TimeoutError("Timeout while reading")

    # ---- Handshake related ----

    def _send_handshake(self, data):
        self._send_base(data, syn=True, fin=False)

    def _read_handshake(self):
        try:
            segment, external_address = self._read_base()
        except TimeoutError:
            raise TimeoutError("Timeout while reading handshake")

        return ApplicationHeaderRDT.from_bytes(segment.data), external_address

    def _base_handshake_messages_exchange(
        self, initial_app_header: ApplicationHeaderRDT
    ):
        self._send_handshake(initial_app_header.as_bytes())
        try:
            received_app_header, external_address = self._read_handshake()
            self.external_host = external_address[0]
            self.external_port = external_address[1]
        except TimeoutError:
            raise TimeoutError("Timeout while reading handshake")

        if not initial_app_header.equals(received_app_header):
            raise ValueError("Handshake failed")

    def _client_handshake_messages_exchange(self, app_header_client):
        try:
            self._base_handshake_messages_exchange(app_header_client)
            self._send_handshake(app_header_client.as_bytes())
        except TimeoutError:
            raise TimeoutError("Timeout while reading handshake")

    def _server_handshake_messages_exchange(
        self, initial_app_header_client
    ):
        self._base_handshake_messages_exchange(initial_app_header_client)

    #
    def run_handshake_as_initiator(self, transfer_type: SelectedTransferType):
        app_header_client = ApplicationHeaderRDT(
            transfer_type,
            self.protocol, 'nombre',
            1000,
            b'\x02\x80\xf4\x02\x02\x02\x02\x02\x02\x02\x02\x02\x02\x02\x02\x02\x02\x02\x02\x02'  # noqa: E501
        )

        # Start message exchange
        retries = 0
        while retries < self.MAX_HANDSHAKE_TIMEOUT_RETRIES:
            try:
                self._client_handshake_messages_exchange(
                    app_header_client)
                return
            except TimeoutError:
                logging.debug("Timeout, retrying")
                retries += 1
            except ValueError:
                logging.debug("Invalid packet retrying")
                retries += 1

        if retries == self.MAX_HANDSHAKE_TIMEOUT_RETRIES:
            logging.error("Connection exhausted {} retries".format(
                self.MAX_HANDSHAKE_TIMEOUT_RETRIES))
            raise TimeoutError(
                "Connection not established after {} retries".format(
                    self.MAX_HANDSHAKE_TIMEOUT_RETRIES)
            )
    #

    def run_handshake_as_listener(
            self, app_header_client: ApplicationHeaderRDT
    ):

        # Start message exchange
        retries = 0
        while retries < self.MAX_HANDSHAKE_TIMEOUT_RETRIES:
            try:
                self._server_handshake_messages_exchange(
                    app_header_client
                )
                break
            except TimeoutError:
                logging.debug("Timeout, retrying")
                retries += 1
            except ValueError:
                logging.debug("Invalid packet retrying")
                retries += 1

    def _update_stream(self, header: HeaderRDT):
        self.ack_num = header.seq_num + 1
        self.seq_num += header.data_size
        # TODO añadir checks


# Cliente -> ACK: 0,            SQN: 999 ,     DATA: ""
# Server  -> ACK: 999   -1,     SQN: 2011,     DATA: ""
# Cliente -> ACK: 2011 - 1,     SQN: 999 ,     DATA: ""

# Server  -> ACK: 999  - 1,     SQN: 2011,      DATA: "a"
# Cliente -> ACK: 2011 - 1,     SQN: 999  + 1,  DATA: "b"
# Server  -> ACK: 1000 - 1,     SQN: 2011 + 1,  DATA: "a"
# Cliente -> ACK: 2011 - 1,     SQN: 999  + 1,  DATA: "b"
# Server  -> ACK: 1000 - 1,     SQN: 2011 + 1,  DATA: "a"
# Cliente -> ACK: 2011 - 1,     SQN: 999  + 1,  DATA: "b"
