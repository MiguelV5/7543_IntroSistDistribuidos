import ctypes


class SelectedProtocol:
    STOP_AND_WAIT: ctypes.c_int8 = 0
    SELECTIVE_REPEAT: ctypes.c_int8 = 1


class SelectedTransferType:
    UPLOAD: ctypes.c_int8 = 0
    DOWNLOAD: ctypes.c_int8 = 1


# DEFAULT FILE PATHS
DEFAULT_SV_STORAGE = './misc/sv_storage/'
DEFAULT_DOWNLOAD_DST = './misc/downloads/'

# DEFAULT ADDRESSES
LOCALHOST = 'localhost'
DEFAULT_SV_PORT = 14000


# DEFAULT TIMEOUTS
DEFAULT_SOCKET_RECV_TIMEOUT = 0.1

# DEFAULT_TIMEOUT_FOR_FILE_RECEIVING_SIDE = 0.5
# DEFAULT_TIMEOUT_FOR_FILE_SENDING_SIDE = 0.2
