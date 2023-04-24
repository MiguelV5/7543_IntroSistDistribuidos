import logging


class FileHandlerError(Exception):
    pass


# Mainly an exception handler for whenever an error occurs at
# basic file operations
# Instantiation of this class will open the given file
class FileHandler:

    ALL_DATA = -1
    MAX_READ_SIZE = 2**20

    def __init__(self, file_path: str, mode: str):
        self.file_path = file_path
        self.mode = mode
        try:
            self.file = open(file_path, mode)
            logging.debug("Opened file: " + file_path)
        except Exception as e:
            logging.error(e)
            logging.error("Error opening file: " + file_path)
            raise FileHandlerError("Error opening file")

    def read(self, read_size):
        try:
            data = self.file.read(read_size)
            logging.debug(
                f"Reading {read_size} bytes from file: {self.file_path}"
            )
            return data
        except Exception:
            logging.error("Error reading from file: " + self.file_path)
            raise FileHandlerError("Error reading from file")

    def write(self, data):
        try:
            self.file.write(data)
            logging.debug(f"Wrote {len(data)} bytes to file: {self.file_path}")
        except Exception:
            logging.error("Error writing to file: " + self.file_path)
            raise FileHandlerError("Error writing to file")

    def close(self):
        self.file.close()
        logging.debug("Closed file: " + self.file_path)
