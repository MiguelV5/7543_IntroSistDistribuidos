from lib.constant import SelectedProtocol
from lib.log_setup import configure_logger
from lib.parser import parse_server_args
from lib.server import ServerRDT


def main():
    args = parse_server_args()
    configure_logger(args, "server.log")

    protocol = SelectedProtocol.SELECTIVE_REPEAT if args.selective_repeat else SelectedProtocol.SELECTIVE_REPEAT 

    # create new server from class
    server = ServerRDT(args.host, args.port, protocol)
    server.run()


if __name__ == "__main__":
    main()
