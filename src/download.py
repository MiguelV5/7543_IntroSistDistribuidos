from lib.log_setup import configure_logger
from lib.parser import parse_download_args


if __name__ == "__main__":

    args = parse_download_args()
    configure_logger(args, "download.log")
