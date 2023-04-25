from lib.constant import SelectedProtocol
from lib.file_handling import FileHandler
from lib.log_setup import configure_logger
from lib.parser import parse_upload_args
from lib.client import ClientRDT


def main():
    args = parse_upload_args()
    configure_logger(args, "upload.log")

    protocol = SelectedProtocol.SELECTIVE_REPEAT if args.selective_repeat else SelectedProtocol.STOP_AND_WAIT

    client = ClientRDT(args.host, args.port, protocol)
    client.upload(args.file_path, args.file_name)


if __name__ == "__main__":
    main()
