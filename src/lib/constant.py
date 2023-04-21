import ctypes


class SelectedProtocol:
    STOP_AND_WAIT: ctypes.c_int8 = 0
    SELECTIVE_REPEAT: ctypes.c_int8 = 1


class SelectedTransferType:
    UPLOAD: ctypes.c_int8 = 0
    DOWNLOAD: ctypes.c_int8 = 1


# DEFAULT FILE PATHS
DEFAULT_SV_STORAGE = './misc/sv_storage'
DEFAULT_DOWNLOAD_DST = './misc/downloads'
DEFAULT_UPLOAD_SRC = './misc/files_to_upload'

# DEFAULT ADDRESSES
LOCALHOST = 'localhost'
DEFAULT_SV_PORT = 14000


# DEFAULT TIMEOUTS
DEFAULT_TIMEOUT = 0.1
