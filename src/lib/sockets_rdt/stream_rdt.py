import logging
import socket
from typing import Tuple
from lib.utils.constant import DEFAULT_INITIATOR_SOCKET_READ_HANDSAKE_TIMEOUT, DEFAULT_LISTENER_SOCKET_READ_HANDSAKE_TIMEOUT, DEFAULT_SOCKET_READ_TIMEOUT,  SelectedProtocol
from lib.utils.exceptions import AssumeAlreadyConnectedError, ExternalConnectionClosed
from lib.segment_encoding.header_rdt import HeaderRDT
from lib.segment_encoding.segment_rdt import SegmentRDT
from lib.protocols.stop_and_wait import StopAndWait, SelectiveRepeat


class StreamRDT():

    START_ACK = 0
    START_LISTENER_SEQ = 1000
    START_CONNECT_SEQ = 2000

    MAX_INITIATOR_HANDSHAKE_TIMEOUT_RETRIES = 4
    MAX_LISTENER_HANDSHAKE_TIMEOUT_RETRIES = 8

    MAX_READ_TIMEOUT_RETRIES = 3
    MAX_CLOSE_RETRIES = 5

    def __init__(self, selected_protocol, external_host, external_port,
                 seq_num, ack_num, host, port=None):

        self.external_host = external_host
        self.external_port = external_port

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('', 0 if port is None else port))
        self.socket.settimeout(DEFAULT_SOCKET_READ_TIMEOUT)

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

    def close(self):
        # self.close_external_connection()
        self.socket.close()

    # ======================== FOR PRIVATE USE ========================

    def _select_protocol(self):
        mss = SegmentRDT.get_max_segment_size()
        protocol = StopAndWait(self, mss)
        if self.selected_protocol == SelectedProtocol.SELECTIVE_REPEAT:
            logging.debug("[PROTOCOL] Selected protocol: Selective Repeat")
            protocol = SelectiveRepeat(self, 5, mss)
        else:
            logging.debug("[PROTOCOL] Selected protocol: Stop and Wait")
        return protocol

    def _check_address(
        self, external_address
    ):
        if external_address[0] != self.external_host:
            raise ValueError("Invalid external host")
        elif external_address[1] != self.external_port:
            raise ValueError("Invalid external_port")

    def read_segment(self, check_address) -> Tuple[SegmentRDT, tuple]:
        return self._base_read_segment(check_address, False)

    def read_segment_non_blocking(self, check_address) -> Tuple[SegmentRDT, tuple]:
        self.settimeout(0)
        try:
            result = self._base_read_segment(
                check_address, True)
        except Exception:
            result = (None, None)
        self.settimeout(DEFAULT_SOCKET_READ_TIMEOUT)
        return result

    def _base_read_segment(self, check_address, expected_syn) -> Tuple[SegmentRDT, tuple]:
        try:
            segment_as_bytes, external_address = self.socket.recvfrom(
                SegmentRDT.MAX_DATA_SIZE + HeaderRDT.size())
            logging.debug("[READ SEGMENT] Received data from {}:{} ->  {}:{}".format(
                external_address[0], external_address[1], self.host, self.port)
            )
        except socket.timeout:
            raise TimeoutError("[READ SEGMENT] Timeout while reading")
        except Exception as e:
            raise ValueError(
                "[READ SEGMENT] Error while reading: " + str(e))

        if (check_address):
            self._check_address(external_address)

        segment = SegmentRDT.from_bytes(segment_as_bytes)
        logging.debug(f"[READ SEGMENT] Received segment {segment}")

        if (expected_syn != segment.header.syn):
            raise ValueError(
                "[READ SEGMENT] Invalid segment received: SYN flag set")

        # CERRAR PROLIJAMENTE
        if segment.header.fin:
            # three/four way close
            raise ExternalConnectionClosed(
                "[READ SEGMENT] Connection closed by external host")

        return segment, external_address

    def send_segment(self, data: bytes, seq_num, ack_num, syn, fin):

        logging.debug("[SEND SEGMENT] Sending data from {}:{} ->  {}:{}".format(
            self.host, self.port, self.external_host, self.external_port))

        header = HeaderRDT(self.selected_protocol, len(data),
                           seq_num, ack_num, syn, fin)
        segment = SegmentRDT(header, data)

        self.socket.sendto(
            segment.as_bytes(),
            (self.external_host, self.external_port)
        )

        logging.debug(f"[SEND SEGMENT] Sending segment {segment}")

    # ---- Handshake related ----

    def _send_handshake(self):
        self.send_segment(b'', self.seq_num, self.ack_num, syn=True, fin=False)

    def _read_handshake(self):
        try:
            segment, external_address = self._base_read_segment(
                False, True)
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
        retries = 0
        while retries < self.MAX_INITIATOR_HANDSHAKE_TIMEOUT_RETRIES:
            try:
                self.settimeout(DEFAULT_INITIATOR_SOCKET_READ_HANDSAKE_TIMEOUT)
                self._initiatior_handshake_messages_exchange()
                self.settimeout(DEFAULT_SOCKET_READ_TIMEOUT)
                return
            except (ValueError, TimeoutError):
                retries += 1

        logging.error("Connection exhausted {} retries".format(
            self.MAX_INITIATOR_HANDSHAKE_TIMEOUT_RETRIES))
        raise TimeoutError(
            "Connection not established after {} retries".format(
                self.MAX_INITIATOR_HANDSHAKE_TIMEOUT_RETRIES)
        )

    def _run_handshake_as_listener(
            self
    ):
        retries = 0
        while retries < self.MAX_LISTENER_HANDSHAKE_TIMEOUT_RETRIES:
            try:
                self.settimeout(DEFAULT_LISTENER_SOCKET_READ_HANDSAKE_TIMEOUT)
                self._listener_handshake_messages_exchange()
                self.settimeout(DEFAULT_SOCKET_READ_TIMEOUT)
                return
            except (ValueError, TimeoutError):
                retries += 1

        logging.error("Connection exhausted {} retries".format(
            self.MAX_LISTENER_HANDSHAKE_TIMEOUT_RETRIES))
        raise TimeoutError(
            "Connection not established after {} retries".format(
                self.MAX_LISTENER_HANDSHAKE_TIMEOUT_RETRIES)
        )

    # ---- Close related ----

    # FALTA ARREGLAR
    def close_external_connection(self):
        logging.debug(
            f"[CLOSE] Closing external connection with ({self.external_host}:{self.external_port})")
        retries = 0
        while retries < self.MAX_CLOSE_RETRIES:
            self.send_segment(b'', self.seq_num, self.ack_num, False, True)
            try:
                segment, external_address = self._base_read_segment(
                    True, False)
                self._check_address(external_address)
                if segment.header.fin:
                    logging.debug("[CLOSE] External connection closed")
                    break
                else:
                    retries += 1
                    continue
            except (TimeoutError, ValueError):
                retries += 1
                continue
            except ExternalConnectionClosed:
                logging.debug("[CLOSE] External connection closed")
                break
