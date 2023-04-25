from lib.client import ClientRDT
from lib.utils.constant import SelectedProtocol
from lib.utils.log_setup import configure_logger
from lib.utils.parser import parse_download_args


if __name__ == "__main__":

    args = parse_download_args()
    configure_logger(args, "download.log")

    protocol = SelectedProtocol.SELECTIVE_REPEAT if args.selective_repeat else SelectedProtocol.STOP_AND_WAIT

    client = ClientRDT(args.host, args.port, protocol)
    client.download(args.dst, args.name)
