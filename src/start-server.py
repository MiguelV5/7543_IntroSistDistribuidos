from lib.parser import parse_server_args
from lib.server import ServerRDT

def main():
    args = parse_server_args()

    # create new server from class
    server = ServerRDT(args.host, args.port)
    server.create()

if __name__ == "__main__":
    main()
