import logging


class SlidingWindow:

    def __repr__(self):
        return f"SlidingWindow(current_seq_num={self.current_seq_num}, final_seq_num={self.final_seq_num}, ack_list={self.ack_list}, sent_list={self.sent_list})"

    def __str__(self):
        return self.__repr__()

    def __init__(self, window_size, initial_seq_num=0):
        self.window_size = window_size
        self.data = []
        self.current_seq_num = initial_seq_num
        self.final_seq_num = initial_seq_num + len(self.data) - 1

        self.ack_list = [False for _ in range(self.window_size)]
        self.sent_list = [False for _ in range(self.window_size)]

    def add_data(self, data):
        self.final_seq_num = self.final_seq_num + len(data)
        self.data += data

    def get_ack(self, received_ack):
        return self.ack_list[received_ack - self.current_seq_num]

    def set_ack(self, received_ack):
        if (received_ack < self.current_seq_num or received_ack > self.final_seq_num):
            return
        self.ack_list[received_ack - self.current_seq_num] = True
        logging.debug(f"[SLIDING WDW] Sliding Window before update: {self}")
        self.update_sliding_window()
        logging.debug(f"[SLIDING WDW] Sliding Window after update: {self}")

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

    def finished(self):
        return self.current_seq_num > self.final_seq_num

    def is_available_segment_to_send(self, seq_num):
        return (self.get_sent(seq_num) is False) and (self.get_ack(seq_num) is False)

    def has_available_segments_to_send(self):
        i = self.current_seq_num
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
            if self.is_available_segment_to_send(i):
                return i, self.data[i - self.current_seq_num]
            i += 1
        return None, None

    def get_current_seq_num(self):
        return self.current_seq_num
