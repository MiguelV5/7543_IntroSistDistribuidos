

import logging
from lib.sockets_rdt.stream_rdt import StreamRDT


class SlidingWindow:
    def __init__(self, data, window_size, initial_seq_num=0):
        self.window_size = window_size
        self.data = data
        self.current_seq_num = initial_seq_num
        self.final_seq_num = initial_seq_num + len(data) - 1

        self.ack_list = [False for _ in range(self.window_size)]
        self.sent_list = [False for _ in range(self.window_size)]

    def get_ack(self, seq_num):
        return self.ack_list[seq_num - self.current_seq_num]

    def set_ack(self, seq_num):
        self.ack_list[seq_num - self.current_seq_num] = True
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

        self.data = self.data[positions_to_move:]
        self.current_seq_num += positions_to_move

    def get_sent(self, seq_num):
        return self.sent_list[seq_num - self.current_seq_num]

    def set_sent(self, seq_num, value: bool):
        self.sent_list[seq_num - self.current_seq_num] = value

    # def get_current_window(self):
    #     return self.data[:self.window_size]

        # return {i + self.current_seq_num: self.data[i] for i in range(self.current_seq_num - self.initial_seq_num, min(self.current_seq_num - self.initial_seq_num + self.window_size, len(self.data)))}

    def is_all_data_ack(self):
        return self.current_seq_num == self.final_seq_num

    def is_available_segment_to_send(self, seq_num):
        return (self.get_sent(seq_num) == False) and (self.get_ack(seq_num) == False)

    def has_available_segments_to_send(self):
        i = self.current_seq_num
        while i <= self.current_seq_num + self.window_size:
            if self.is_available_segment_to_send(i):
                return True
            i += 1
        return False

    def reset_sent_segments(self):
        self.sent_list = [False for _ in range(self.window_size)]

    def get_first_available_segment(self):
        i = self.current_seq_num
        while i <= self.current_seq_num + self.window_size:
            if self.is_available_segment_to_send(i):
                return i, self.data[i - self.current_seq_num]
            i += 1
        return None, None


class SelectiveRepeat:

    def __init__(self, stream: StreamRDT, mss: int):
        self.stream = stream
        self.seq_num = self.stream.seq_num
        self.ack_num = self.stream.ack_num
        self.window_size = 5
        self.mss = mss

        # self.acks_segment = {}
        # self.sent_segments = {}

    def send(self, data):
        # separating data into segments by mss
        data_segments = self.get_segment_data(data)
        window = SlidingWindow(
            data_segments, self.window_size, self.seq_num)

        # while there are still segments to send

        retries = 0
        while not window.is_all_data_ack() and retries < self.MAX_TIMEOUT_RETRIES:

            if not window.has_available_segments_to_send():

                try:
                    # read blocking
                    window.set_ack(received_seq_num)
                    retries = 0
                    continue
                except TimeoutError:
                    # resend all segments
                    window.reset_sent_segments()
                    retries += 1
                    continue

            segment, last_sent_seq_num = window.get_first_available_segment()

            # send_segment
            window.set_sent(last_sent_seq_num, True)

            try:
                # received_segment, received_seq_num =  read non blocking
                window.set_ack(received_seq_num)
                retries = 0
                continue
            except TimeoutError:
                continue

                # segments = self.window.get().items()

                # filter de los que envie segments con sent_segments
                # while len(segments) > 0:
                # envio el segmento
                #
                # recibo el ack bloqueante con timeout de 1 segundo

                # sending segments
                # sl = actual_window.items()
                # while len(sl) > 0:
                #     seq_num, segment = sl.
                #     logging.info(f"Sending segment {seq_num}")
                #     # sending each segment with its own seq_num
                #     self.stream.send_segment(segment, seq_num, self.ack_num, False, False)
                #     # receiving acks non blocking
                #     segment = self.stream.receive_segment_non_blocking()
                #     if segment is not None:
                #         # if ack received, move window
                #         logging.info(f"Received ack {segment.header.ack_num}")
                #         # an ack was received, we save the ack in the acks dict
                #         acks[segment.header.ack_num] = True
                #         self.window.move()
                #         buffer = self.window.get()

    def get_segment_data(self, data):
        # separating data into segments by mss
        data_segments = []
        for i in range(0, len(data), self.mss):
            data_segments.append(data[i: i + self.mss])
        return data_segments

    def filter_segments(self, segments):
        segments = []
        for seq_num, segment in segments:
            if seq_num in self.sent_segments:
                del segments[seq_num]
