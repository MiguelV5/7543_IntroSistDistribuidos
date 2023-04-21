import logging
import socket

# create a stop and wait protocol


class StopAndWait():
    def __init__(self, socket, addr, timeout=0.1, debug=False):
        self.socket = socket
        # maximum segment size
        self.mss = 1024
        # sequence number alternating bit
        self.seq = 0
        # acknowledgement number
        self.ack = 0
        # timeout in ms
        self.timeout = timeout

        self.segment_data = None
        # last acknowledgement number
        self.last_ack = 0
        # last sequence number
        self.last_seq = None
        # last data
        self.last_segment_data = None
        # address
        self.addr = addr
        # header with sequence number and acknowledgement number
        self.header = {}
        self.header["sqn"] = 1
        self.header["ack"] = 2

        self.debug = debug

    def send(self, data):
        # separate data into segments
        data = [data[i:i+self.mss] for i in range(0, len(data), self.mss)]
        # send each segment
        for idx, segment in enumerate(data):
            if self.debug:
                logging.info("Sending chunk index: {}".format(idx))
            self.send_segment(self.encodePacket(self.seq, 0, segment))

        # send empty segment to indicate end of transmission
        self.send_segment(self.encodePacket(self.seq, 0, b''))

    def send_segment(self, packet):
        # send data
        sent = self.socket.send(packet)
        if sent == 0:
            raise RuntimeError("socket connection broken")
        # wait for receiver acknowledgement
        while True:
            self.socket.settimeout(self.timeout)
            try:
                ackPacket, _ = self.socket.recvfrom(
                    self.mss + len(self.header))
                # TODO: check if the acknowledgement is from the
                # correct address
                logging.info(
                    "Received acknowledgement from: {}".format(self.addr))
                # check if data has been acknowledged
                sq, ackNum, _ = self.decodePacket(ackPacket)
                logging.info(
                    "Acknowledgement sequence: {} acknowledgement number: {}"
                    .format(sq, ackNum)
                )
                if ackNum == 1 and sq == self.seq:
                    if self.debug:
                        logging.info(
                            "Chunk acknowledged sequence: {}".format(self.seq))
                    # increment sequence number alternating bit
                    self.last_seq = sq
                    self.last_segment_data = packet
                    self.seq = (self.seq + 1) % 2
                    break
            except socket.timeout:
                if self.debug:
                    logging.info(
                        "Timeout reached, resending chunk for seq: {}"
                        .format(self.seq)
                    )
                # If the acknowledgment is not received within the timeout
                # period, resend the packet resend data
                self.socket.send(packet)
                continue

    def send_ack(self, sequence_number, address):
        # send acknowledgement
        ack_packet = self.encodePacket(sequence_number, 1, b'')
        # print(str(ack_packet))
        self.socket.sendto(ack_packet, address)

    def receive(self, data, addr):
        sq, _, decodedData = self.decodePacket(data)
        logging.info(
            "Received packet sequence: {} from addr: {}".format(sq, addr))
        if len(decodedData) == 0:
            # end of transmission
            self.send_ack(sq, addr)
            self.last_seq = sq
            return b''
        if (self.last_seq is not None) and (sq == self.last_seq):
            # we have received a duplicate packet
            if self.debug:
                logging("Received duplicate packet sequence: {}"
                        .format(self.seq)
                        )

        # send acknowledgement to address
        self.send_ack(sq, addr)
        self.last_seq = sq
        return decodedData

    def decodePacket(self, data):
        # get sequence number from the first bit of the data
        firstByte = int.from_bytes(data[:1], 'big')
        sequenceNumber = firstByte >> 7
        # get acknowledgement number from the second bit of the data
        ackMask = (1 << 6)
        ackNum = (firstByte & ackMask) >> 6
        # get data from the rest of the data
        data = data[2:]
        return sequenceNumber, ackNum, data

    def encodePacket(self, sq, ack, data):
        # encode sequence number
        sq = sq << 7
        # encode acknowledgement number
        ack = ack << 6
        header = (sq | ack).to_bytes(1, 'big')
        return header + data
