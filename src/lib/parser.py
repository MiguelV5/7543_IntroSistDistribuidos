import argparse
from lib.constant import (DEFAULT_DOWNLOAD_DST,
                          DEFAULT_SV_STORAGE, LOCALHOST,
                          DEFAULT_SV_PORT)

# ====================== Pub functions ======================


# Returns an object containing all parsed args for the server program
def parse_server_args():
    parser = _get_parser_with_common_args("Start the server")

    parser.add_argument(
        "-s",
        "--storage",
        default=DEFAULT_SV_STORAGE,
        help="specify the server's storage path",
    )

    args = parser.parse_args()

    return args


# Returns an object containing all parsed args for the upload program
def parse_upload_args():
    parser = _get_parser_for_client_programs("Upload a file to the server")

    parser.add_argument(
        "-s", "--src", dest="src", metavar="FILEPATH",
        required=True,
        help="path to the file to upload"
    )

    args = parser.parse_args()

    return args


# Returns an object containing all parsed args for the download program
def parse_download_args():
    parser = _get_parser_for_client_programs("Download a file from the server")

    parser.add_argument(
        "-d", "--dst", dest="dst", metavar="FILEPATH",
        default=DEFAULT_DOWNLOAD_DST,
        help="destination file path"
    )

    args = parser.parse_args()

    return args


# ====================== Priv functions ======================

# Returns a parser with the common arguments for the client and server
def _get_parser_with_common_args(command_description: str):
    parser = argparse.ArgumentParser(description=command_description)
    exclusive_group = parser.add_mutually_exclusive_group()
    # group to require only one of the two following arguments
    exclusive_group.add_argument(
        "-v", "--verbose", action="store_true",
        help="increase output verbosity"
    )
    exclusive_group.add_argument(
        "-q", "--quiet", action="store_true", help="decrease output verbosity"
    )

    parser.add_argument(
        "-H",
        "--host",
        default=LOCALHOST,
        metavar="ADDR",
        help="the server's listening IP address",
    )

    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=DEFAULT_SV_PORT,
        help="the server's listening port",
    )

    exclusive_group2 = parser.add_mutually_exclusive_group()
    exclusive_group2.add_argument(
        "-saw",
        "--stop_and_wait",
        action='store_true',
        help="choose Stop and Wait transference")
    exclusive_group2.add_argument(
        "-sr",
        "--selective_repeat",
        action='store_true',
        help="choose Selective Repeat transference")

    return parser


# Returns a parser with the common arguments for
# the client programs (upload and download)
def _get_parser_for_client_programs(command_description: str):
    parser = _get_parser_with_common_args(command_description)

    parser.add_argument(
        "-n", "--name",
        dest="name",
        required=True,
        metavar="FILENAME",
        help="name of the file to request to the server"
    )

    return parser
