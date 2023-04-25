import logging
from lib.protocols.utils.buffer_sorter import BufferSorter

from lib.protocols.utils.sliding_window import SlidingWindow


class SelectiveRepeat:

    MAX_TIMEOUT_RETRIES = 5

    def __init__(self, stream, window_size, mss: int):
        self.stream = stream
        self.window_size = window_size
        self.mss = mss

    # ======================== FOR PUBLIC USE ========================

    def send(self, data_segments):
        window = SlidingWindow(
            data_segments, self.window_size, self.stream.seq_num)

        retries = 0
        while not window.finished() and retries < SelectiveRepeat.MAX_TIMEOUT_RETRIES:
            if not window.has_available_segments_to_send():
                try:
                    received_segment, external_address = self.stream.read_segment(
                        True)
                    self._update_protocol(
                        received_segment, external_address, window)
                    continue
                except TimeoutError:
                    window.reset_sent_segments()
                    retries += 1
                    continue
                except ValueError:
                    continue

            self._send_segment(window)

            received_segment, external_address = self.stream.read_segment_non_blocking(
                True)
            if received_segment is None:
                continue

            self._update_protocol(
                received_segment, external_address, window)
            retries = 0

        if retries >= SelectiveRepeat.MAX_TIMEOUT_RETRIES:
            raise TimeoutError(
                "[PROTOCOL] Multiple timeouts while tryng to send data and receive corresponding acks"
            )

    def read(self):

        buffer_sorter = BufferSorter(self.stream.ack_num)

        retries = 0
        while retries < SelectiveRepeat.MAX_TIMEOUT_RETRIES:
            try:
                received_segment, _ = self.stream.read_segment(
                    True)
            except TimeoutError:
                retries += 1
                continue
            except ValueError:
                continue

            self._send_ack(buffer_sorter, received_segment)
            logging.debug(
                f"[PROTOCOL] Stream ack after pop: {self.stream.ack_num}")

            self.stream.ack_num, data = buffer_sorter.pop_available_data()
            return data

        if retries >= SelectiveRepeat.MAX_TIMEOUT_RETRIES:
            raise TimeoutError(
                "[PROTOCOL] Multiple timeouts while tryng to read data")

    # ======================== FOR PRIVATE USE ========================

    def _update_protocol(self, received_segment, external_addresss, window: SlidingWindow):
        logging.debug(
            f"[PROTOCOL] Received segment {received_segment} from {external_addresss}")
        window.set_ack(received_segment.header.ack_num)
        self.stream.seq_num = window.get_current_seq_num()

    def _send_segment(self, window: SlidingWindow):
        sent_seq_num, segment = window.get_first_available_segment()
        self.stream.send_segment(
            segment, sent_seq_num, self.stream.ack_num, False, False)
        window.set_sent(sent_seq_num, True)

    def _send_ack(self, buffer_sorter: BufferSorter, received_segment):
        self.stream.send_segment(
            b'', self.stream.seq_num, received_segment.header.seq_num, False, False)
        buffer_sorter.add_segment(
            received_segment.header.seq_num, received_segment.data)
