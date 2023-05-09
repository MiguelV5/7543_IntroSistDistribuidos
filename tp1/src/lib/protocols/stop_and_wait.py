from lib.protocols.selective_repeat import SelectiveRepeat


class StopAndWait():

    def __init__(self, stream, mss):
        self.stream = stream
        self.mss = mss
        self.selective_repeat = SelectiveRepeat(stream, 1, mss)

    def send(self, data):
        self.selective_repeat.send(data)

    def read(self):
        return self.selective_repeat.read()
