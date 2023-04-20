from lib.log_setup import configure_logger
from lib.parser import parse_server_args
from lib.server import ServerRDT


def main():
    args = parse_server_args()
    configure_logger(args, "server.log")

    # create new server from class
    server = ServerRDT(args.host, args.port)
    server.run()


if __name__ == "__main__":
    main()
