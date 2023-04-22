

import logging
from lib.sockets_rdt.stream_rdt import StreamRDT


class SlidingWindow:
    def __init__(self, data, window_size, initial_seq_num = 0):
        self.window_size = window_size
        self.data = data
        self.initial_seq_num = initial_seq_num
        self.current_index = initial_seq_num
        self.final_seq_num = initial_seq_num + len(data)
        
    def get(self):
        return {i + self.current_index: self.data[i] for i in range(self.current_index - self.initial_seq_num, min(self.current_index - self.initial_seq_num + self.window_size, len(self.data)))}

    def move(self):
        self.current_index += 1   
        
    def isEmpty(self):
        return self.current_index == self.final_seq_num
        


class SelectiveRepeat:

    def __init__(self, stream: StreamRDT, mss: int):
        self.stream = stream
        self.seq_num = self.stream.seq_num
        self.ack_num = self.stream.ack_num
        self.window_size = 5
        self.window = None
        self.mss = mss
        
        self.acks_segment = {}
        self.sent_segments = {}

    def send(self, data):
        # separating data into segments by mss
        data_segments = self.get_segment_data(data)
        self.window = SlidingWindow(data_segments, self.window_size, self.seq_num)

        # while there are still segments to send
        
        while not self.window.isEmpty():
            segments = self.window.get().items()
            # filter de los que envie segments con sent_segments
            while len(segments) > 0:
                # envio el segmento
                # 
            # recibo el ack bloqueante con timeout de 1 segundo

            
            
            # sending segments
            sl = actual_window.items()
            while len(sl) > 0:
                seq_num, segment = sl.
                logging.info(f"Sending segment {seq_num}")
                # sending each segment with its own seq_num
                self.stream.send_segment(segment, seq_num, self.ack_num, False, False)
                # receiving acks non blocking
                segment = self.stream.receive_segment_non_blocking()
                if segment is not None:
                    # if ack received, move window
                    logging.info(f"Received ack {segment.header.ack_num}")
                    # an ack was received, we save the ack in the acks dict
                    acks[segment.header.ack_num] = True
                    self.window.move()
                    buffer = self.window.get()
                    
    def get_segment_data(self, data):
         # separating data into segments by mss
        data_segments = []
        for i in range(0, len(data), self.mss):
            data_segments.append(data[i:i + self.mss])
        return data_segments

    def filter_segments(self, segments):
        segments = []
        for seq_num, segment in segments:
            if seq_num in self.sent_segments:
                del segments[seq_num]
    
        
            
