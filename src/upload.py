from lib.log_setup import configure_logger
from lib.parser import parse_upload_args
from lib.client import ClientRDT
import logging


def main():
    args = parse_upload_args()
    configure_logger(args, "upload.log")

    try:
        client = ClientRDT(args.host, args.port)
    except Exception as e:
        logging.error("Error: " + str(e))
        exit(1)
    # tratar de abrir el archivo que pidio el user
    # obtener la data como bytes
    # cambiar el metodo de upload para que tome los datos y el nombre del archivo
    client.upload()


if __name__ == "__main__":
    main()
