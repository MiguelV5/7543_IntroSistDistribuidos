from lib.utils.constant import SelectedProtocol
from lib.utils.log_setup import configure_logger
from lib.utils.parser import parse_upload_args
from lib.client import ClientRDT


def main():
    args = parse_upload_args()
    configure_logger(args, "upload.log")

    protocol = SelectedProtocol.SELECTIVE_REPEAT if args.selective_repeat else SelectedProtocol.STOP_AND_WAIT

    client = ClientRDT(args.host, args.port, protocol)
    client.upload(args.src, args.name)


if __name__ == "__main__":
    main()
