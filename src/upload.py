from lib.constant import SelectedProtocol
from lib.log_setup import configure_logger
from lib.parser import parse_upload_args
from lib.client import ClientRDT
import logging


def main():
    args = parse_upload_args()
    configure_logger(args, "upload.log")

    protocol = SelectedProtocol.SELECTIVE_REPEAT if args.selective_repeat else SelectedProtocol.STOP_AND_WAIT

    client = ClientRDT(args.host, args.port, protocol)

    # tratar de abrir el archivo que pidio el user
    # obtener la data como bytes
    # cambiar el metodo de upload para que tome los datos y el nombre del archivo
    try:
        client.upload(args.name, args.src)
    except Exception as e:
        logging.error("Error uploading file: " + str(e))
        exit(1)


if __name__ == "__main__":
    main()
