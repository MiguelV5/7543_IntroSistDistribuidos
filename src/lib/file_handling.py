import logging


class FileHandlerError(Exception):
    pass


# Mainly an exception handler for whenever an error occurs at
# basic file operations
# Instantiation of this class will open the given file
class FileHandler:

    def __init__(self, file_name: str, mode: str):
        self.file_name = file_name
        self.mode = mode
        try:
            self.file = open(file_name, mode)
            logging.debug("Opened file: " + file_name)
        except Exception as e:
            logging.error(e)
            logging.error("Error opening file: " + file_name)
            raise FileHandlerError("Error opening file")

    def read(self, read_size):
        try:
            data = self.file.read(read_size)
            logging.debug(
                f"Reading {read_size} bytes from file: {self.file_name}"
            )
            return data
        except Exception:
            logging.error("Error reading from file: " + self.file_name)
            raise FileHandlerError("Error reading from file")

    def write(self, data):
        try:
            self.file.write(data)
            logging.debug(f"Wrote {len(data)} bytes to file: {self.file_name}")
        except Exception:
            logging.error("Error writing to file: " + self.file_name)
            raise FileHandlerError("Error writing to file")

    def close(self):
        self.file.close()
        logging.debug("Closed file: " + self.file_name)
