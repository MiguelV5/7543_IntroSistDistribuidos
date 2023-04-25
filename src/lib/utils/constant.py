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
DEFAULT_SOCKET_READ_TIMEOUT = 0.75

DEFAULT_LISTENER_SOCKET_READ_HANDSAKE_TIMEOUT = 0.5
DEFAULT_INITIATOR_SOCKET_READ_HANDSAKE_TIMEOUT = DEFAULT_LISTENER_SOCKET_READ_HANDSAKE_TIMEOUT * 3

DEFAULT_RECEIVER_SOCKET_READ_CLOSE_TIMEOUT = DEFAULT_INITIATOR_SOCKET_READ_HANDSAKE_TIMEOUT
DEFAULT_INITIATOR_SOCKET_READ_CLOSE_TIMEOUT = DEFAULT_LISTENER_SOCKET_READ_HANDSAKE_TIMEOUT
