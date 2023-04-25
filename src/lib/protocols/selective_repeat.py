import logging

from lib.exceptions import ExternalConnectionClosed


class SlidingWindow:

    def __repr__(self):
        return f"SlidingWindow(current_seq_num={self.current_seq_num}, final_seq_num={self.final_seq_num}, ack_list={self.ack_list}, sent_list={self.sent_list})"

    def __str__(self):
        return self.__repr__()

    def __init__(self, data, window_size, initial_seq_num=0):
        self.window_size = window_size
        self.data = data
        self.current_seq_num = initial_seq_num
        self.final_seq_num = initial_seq_num + len(data) - 1

        self.ack_list = [False for _ in range(self.window_size)]
        self.sent_list = [False for _ in range(self.window_size)]

    def get_ack(self, received_ack):
        return self.ack_list[received_ack - self.current_seq_num]

    def set_ack(self, received_ack):
        if (received_ack < self.current_seq_num or received_ack > self.final_seq_num):
            return
        self.ack_list[received_ack - self.current_seq_num] = True
        self.update_sliding_window()

    def update_sliding_window(self):
        positions_to_move = 0
        for ack in self.ack_list:
            if ack:
                positions_to_move += 1
            else:
                break

        self.ack_list = self.ack_list[positions_to_move:]
        for _ in range(positions_to_move):
            self.ack_list.append(False)

        self.sent_list = self.sent_list[positions_to_move:]
        for _ in range(positions_to_move):
            self.sent_list.append(False)

        print(f">>>>>>>> PRE UPDATED current_seq_num: {self.current_seq_num}")
        self.data = self.data[positions_to_move:]
        self.current_seq_num += positions_to_move
        print(f">>>>>>>> UPDATED current_seq_num: {self.current_seq_num}")

    def get_sent(self, seq_num):
        return self.sent_list[seq_num - self.current_seq_num]

    def set_sent(self, seq_num, value: bool):
        self.sent_list[seq_num - self.current_seq_num] = value

    def finished(self):
        # finished when all data is ack and current seq num is final seq num
        return self.current_seq_num == self.final_seq_num + 1

    def is_available_segment_to_send(self, seq_num):
        return (self.get_sent(seq_num) is False) and (self.get_ack(seq_num) is False)

    def has_available_segments_to_send(self):
        i = self.current_seq_num
        # is there any segment that is not sent and not ack in
        # the current window?
        while (i <= self.final_seq_num) and (i < self.current_seq_num + self.window_size):
            if self.is_available_segment_to_send(i):
                return True
            i += 1
        return False

    def reset_sent_segments(self):
        self.sent_list = [False for _ in range(self.window_size)]

    def get_first_available_segment(self):
        i = self.current_seq_num
        while (i <= self.final_seq_num) and (i < self.current_seq_num + self.window_size):
            print(
                f">>>>>>>>>>>>>>>>>   i:  {i},  data: {self.data[i - self.current_seq_num]}")
            if self.is_available_segment_to_send(i):

                print(
                    f">>>>>>>>>>>>>>>>>  (IF) i:  {i},  data: {self.data[i - self.current_seq_num]}")

                return i, self.data[i - self.current_seq_num]
            i += 1
        return None, None

    def get_current_seq_num(self):
        return self.current_seq_num


class BufferSorter:

    def __repr__(self):
        return f'BufferSorter(curr_seq_num={self.curr_ack_num}, buffer={self.buffer})'

    def __str__(self):
        return self.__repr__()

    def __init__(self, initial_ack_num=0):
        self.curr_ack_num = initial_ack_num
        self.buffer = []

    def add_segment(self, received_seq_num, data):
        seg_position = received_seq_num - self.curr_ack_num
        if seg_position < 0:
            return
        if seg_position >= len(self.buffer):
            for i in range(seg_position - len(self.buffer) + 1):
                self.buffer.append((len(self.buffer) + i, None))
        self.buffer[seg_position] = (received_seq_num, data)

    def pop_available_data(self):
        data_popped = b''
        while self._has_available_segment_to_pop():
            data = self._pop_first_available_segment()
            data_popped = data_popped + data
        return data_popped

    def _pop_first_available_segment(self):
        if (self._has_available_segment_to_pop() is False):
            return None
        seq_num, data = self.buffer.pop(0)
        self.curr_ack_num = seq_num + 1
        return data

    def _has_available_segment_to_pop(self):
        return len(self.buffer) != 0 and \
            (self.buffer[0][0] == self.curr_ack_num) and \
            (self.buffer[0][1] is not None)

    def get_current_ack_num(self):
        return self.curr_ack_num


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

            self._send_ack(received_segment, buffer_sorter)
            return buffer_sorter.pop_available_data()

        if retries >= SelectiveRepeat.MAX_TIMEOUT_RETRIES:
            raise TimeoutError(
                "[PROTOCOL] Multiple timeouts while tryng to read data")

    # ======================== FOR PRIVATE USE ========================

    def _update_protocol(self, received_segment, external_addresss, window: SlidingWindow):
        logging.info(
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
        self.stream.ack_num = buffer_sorter.get_current_ack_num()
