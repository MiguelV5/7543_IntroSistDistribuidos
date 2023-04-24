

import logging
import socket
from typing import Tuple
from lib.constant import DEFAULT_SOCKET_RECV_TIMEOUT,  SelectedProtocol
from lib.segment_encoding.header_rdt import HeaderRDT
from lib.segment_encoding.segment_rdt import SegmentRDT
from lib.protocols.stop_and_wait import StopAndWait, SelectiveRepeat


class AssumeAlreadyConnectedError(Exception):
    pass


class StreamRDT():

    START_ACK = 0
    START_LISTENER_SEQ = 1000
    START_CONNECT_SEQ = 2000

    MAX_HANDSHAKE_TIMEOUT_RETRIES = 8
    MAX_READ_TIMEOUT_RETRIES = 3
    MAX_CLOSE_RETRIES = 5

    def __init__(self, selected_protocol, external_host, external_port,
                 seq_num, ack_num, host, port=None):

        self.external_host = external_host
        self.external_port = external_port

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('', 0 if port is None else port))
        self.socket.settimeout(DEFAULT_SOCKET_RECV_TIMEOUT)

        self.host = host
        self.port = self.socket.getsockname()[1]

        self.seq_num = seq_num
        self.ack_num = ack_num

        self.selected_protocol = selected_protocol
        self.protocol = self._select_protocol()

    @classmethod
    def from_listener(
        cls, protocol, external_host, external_port,
        segment: SegmentRDT, host, port=None
    ):
        stream = cls(
            protocol, external_host, external_port,
            cls.START_LISTENER_SEQ, segment.header.seq_num,
            host, port,
        )
        stream._run_handshake_as_listener()
        return stream

    @classmethod
    def connect(
        cls, protocol, external_host,
        external_port
    ):
        stream = cls(
            protocol, external_host, external_port, cls.START_CONNECT_SEQ,
            StreamRDT.START_ACK, 'localhost'
        )
        logging.info("[CONNECT] Connecting to {}:{} with my port: {}".format(
            external_host, external_port, stream.port))
        stream._run_handshake_as_initiator()
        return stream

    def settimeout(self, seconds):
        self.socket.settimeout(seconds)

    # ======================== FOR PUBLIC USE ========================

    def send(self, data: bytes):
        mss = SegmentRDT.get_max_segment_size()

        data_segments = []
        for i in range(0, len(data), mss):
            data_segments.append(data[i:i+mss])

        self.protocol.send(data_segments)

    def read(self) -> bytes:
        return self.protocol.read()

    def close_external_connection(self):
        logging.debug("Closing external connection")
        retries = 0
        while retries < self.MAX_CLOSE_RETRIES:
            self.send_segment(b'', self.seq_num, self.ack_num, False, True)
            try:
                segment, external_address = self.read_segment(True)
                self._check_address(external_address)
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

    # ======================== FOR PRIVATE USE ========================

    def _select_protocol(self):
        mss = SegmentRDT.get_max_segment_size()
        protocol = StopAndWait(self, mss)
        if self.selected_protocol == SelectedProtocol.SELECTIVE_REPEAT:
            protocol = SelectiveRepeat(self, 5, mss)
        return protocol

    def _check_address(
        self, external_address
    ):
        if external_address[0] != self.external_host:
            raise ValueError("Invalid external host")
        elif external_address[1] != self.external_port:
            raise ValueError("Invalid external_port")

    def read_segment(self, check_address) -> Tuple[SegmentRDT, tuple]:
        try:
            segment_as_bytes, external_address = self.socket.recvfrom(
                SegmentRDT.MAX_DATA_SIZE + HeaderRDT.size())
            logging.debug("[READ SEGMENT] Received data from {}:{} ->  {}:{}".format(
                external_address[0], external_address[1], self.host, self.port)
            )
            if (check_address):
                self._check_address(external_address)
            segment = SegmentRDT.from_bytes(segment_as_bytes)
            return segment, external_address
        except socket.timeout:
            # logging.debug("Timeout while reading")
            raise TimeoutError("Timeout while reading")
        except ValueError as e:
            logging.debug("Invalid segment received:  " + str(e))
            raise ValueError("Invalid segment received:  " + str(e))

    def read_segment_non_blocking(self, check_address) -> Tuple[SegmentRDT, tuple]:
        try:
            self.socket.settimeout(0)
            segment_as_bytes, external_address = self.socket.recvfrom(
                SegmentRDT.MAX_DATA_SIZE + HeaderRDT.size())
            segment = SegmentRDT.from_bytes(segment_as_bytes)
            if (check_address):
                self._check_address(external_address)
            self.socket.settimeout(DEFAULT_SOCKET_RECV_TIMEOUT)
            return segment, external_address
        except Exception:
            self.socket.settimeout(DEFAULT_SOCKET_RECV_TIMEOUT)
            return None, None

    def send_segment(self, data: bytes, seq_num, ack_num, syn, fin):
        logging.debug("Sending data from {}:{} ->  {}:{}".format(
            self.host, self.port, self.external_host, self.external_port))

        header = HeaderRDT(self.selected_protocol, len(data),
                           seq_num, ack_num, syn, fin)
        segment = SegmentRDT(header, data)

        self.socket.sendto(
            segment.as_bytes(),
            (self.external_host, self.external_port)
        )

    # ---- Handshake related ----

    def _send_handshake(self):
        self.send_segment(b'', self.seq_num, self.ack_num, syn=True, fin=False)

    def _read_handshake(self):
        try:
            segment, external_address = self.read_segment(True)
        except TimeoutError:
            raise TimeoutError(
                "[HANDSHAK READ] Timeout while reading handshake")

        self.external_host = external_address[0]
        self.external_port = external_address[1]
        self.ack_num = segment.header.seq_num
        if self.seq_num != segment.header.ack_num:
            logging.error(
                f"seq_num: {self.seq_num} , ack_num: {segment.header.ack_num}")
            raise ValueError("[HANDSHAK READ] Invalid handshake")
        if not segment.header.syn:
            logging.debug("[HANDSHAK READ] Invalid syn received" +
                          str(segment.header.syn))
            raise AssumeAlreadyConnectedError
        if segment.header.fin:
            logging.error("[HANDSHAK READ] fin: " + str(segment.header.fin))
            raise ValueError("[HANDSHAK READ] Invalid handshake")

        return segment.header

    def _initiatior_handshake_messages_exchange(self):
        self._send_handshake()
        logging.debug("[HANDSHAKE] INITIATOR 1 (send)")

        self._read_handshake()
        logging.debug("[HANDSHAKE] INITIATOR 2 (read)")

        self._send_handshake()
        logging.debug("[HANDSHAKE] INITIATOR 3 (send)")

    def _listener_handshake_messages_exchange(
        self
    ):
        self._send_handshake()
        logging.debug("[HANDSHAKE] LISTENER 2 (send)")

        try:
            self._read_handshake()
        except AssumeAlreadyConnectedError:
            logging.debug("[HANDSHAKE] Already connected")

        logging.debug("[HANDSHAKE] LISTENER 3 (read)")

    def _run_handshake_as_initiator(self):

        # Start message exchange
        retries = 0
        while retries < self.MAX_HANDSHAKE_TIMEOUT_RETRIES:
            try:
                self._initiatior_handshake_messages_exchange()
                return
            except TimeoutError:
                # logging.debug("Timeout, retrying")
                retries += 1
            except ValueError:
                # logging.debug("Invalid packet retrying")
                retries += 1

        logging.error("Connection exhausted {} retries".format(
            self.MAX_HANDSHAKE_TIMEOUT_RETRIES))
        raise TimeoutError(
            "Connection not established after {} retries".format(
                self.MAX_HANDSHAKE_TIMEOUT_RETRIES)
        )

    def _run_handshake_as_listener(
            self
    ):
        retries = 0
        while retries < self.MAX_HANDSHAKE_TIMEOUT_RETRIES:
            try:
                self._listener_handshake_messages_exchange()
                return
            except TimeoutError:
                # logging.debug("Timeout, retrying")
                retries += 1
            except ValueError:
                # logging.debug("Invalid packet retrying")
                retries += 1

        logging.error("Connection exhausted {} retries".format(
            self.MAX_HANDSHAKE_TIMEOUT_RETRIES))
        raise TimeoutError(
            "Connection not established after {} retries".format(
                self.MAX_HANDSHAKE_TIMEOUT_RETRIES)
        )
