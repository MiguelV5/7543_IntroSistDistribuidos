import logging
from lib.utils.constant import SelectedProtocol
from lib.utils.log_setup import configure_logger
from lib.utils.parser import parse_server_args
from lib.server import ServerRDT


def main():
    args = parse_server_args()
    configure_logger(args, "server.log")

    protocol = SelectedProtocol.SELECTIVE_REPEAT if args.selective_repeat else SelectedProtocol.STOP_AND_WAIT

    # create new server from class
    server = ServerRDT(args.host, args.port, protocol)
    try:
        server.run()
    except Exception as e:
        logging.error("Error running server: " + str(e))
        exit(1)


if __name__ == "__main__":
    main()
