from lib.protocols.stop_and_wait import SelectiveRepeat


# create a stop and wait protocol


class StopAndWait():
    
    def __init__(self, stream, mss):
        self.stream = stream
        self.mss = mss
        self.selective_repeat = SelectiveRepeat(stream, 1, mss)
    
    def send(self, data):
        self.selective_repeat.send(data)
    
    
    
    
    
    
    
    
    
