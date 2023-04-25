class BufferSorter:

    def __repr__(self):
        return f'BufferSorter(curr_ack_num={self.curr_ack_num}, buffer={self.buffer})'

    def __str__(self):
        return self.__repr__()

    def __init__(self, initial_ack_num=0):
        self.curr_ack_num = initial_ack_num
        self.buffer = []

    def set_ack_num(self, ack_num):
        self.curr_ack_num = ack_num

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
        last_ack_num = self.curr_ack_num
        while self._has_available_segment_to_pop():
            last_ack_num, data = self._pop_first_available_segment()
            data_popped = data_popped + data
        return last_ack_num, data_popped

    def _pop_first_available_segment(self):
        if (self._has_available_segment_to_pop() is False):
            return self.curr_ack_num, None
        ack_num, data = self.buffer.pop(0)
        self.curr_ack_num = ack_num + 1
        return ack_num, data

    def _has_available_segment_to_pop(self):
        return len(self.buffer) != 0 and \
            (self.buffer[0][0] == self.curr_ack_num) and \
            (self.buffer[0][1] is not None)

    def get_current_ack_num(self):
        return self.curr_ack_num
