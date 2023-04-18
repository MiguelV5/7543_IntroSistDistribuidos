from lib.parser import parse_upload_args
from lib.client import ClientRDT

def main():
    args = parse_upload_args()

    try:
        client = ClientRDT(args.host, args.port)
    except Exception as e:
        print("Error: " + str(e))
        exit(1)
    client.connect()
    client.send(0)

if __name__ == "__main__":
    main()
