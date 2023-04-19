from lib.parser import parse_upload_args
from lib.client import ClientRDT
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Upload")


def main():
    args = parse_upload_args()

    try:
        client = ClientRDT(args.host, args.port)
    except Exception as e:
        logging.error("Error: " + str(e))
        exit(1)
    client.connect()
    client.send(0)


if __name__ == "__main__":
    main()
