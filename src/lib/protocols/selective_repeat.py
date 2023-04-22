

from lib.sockets_rdt.stream_rdt import StreamRDT


class SlidingWindow:
    def __init__(self, data, window_size, initial_seq_num=0):
        self.window_size = window_size
        self.data = data
        self.initial_seq_num = initial_seq_num

    def get(self, seq_num):
        return self.data[seq_num - self.initial_seq_num: seq_num - self.initial_seq_num + self.window_size]


class SelectiveRepeat:

    def __init__(self, stream: StreamRDT):
        self.stream = stream
        self.seq_num = 0
        self.ack_num = 0
        self.window_size = 2
        self.window = Window(self.window_size)
        self.next_seq_num = 0
        self.next_ack_num = 0
        self.last_ack_num = 0
        self.last_ack_time = 0
