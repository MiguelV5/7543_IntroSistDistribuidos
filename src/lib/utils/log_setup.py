import logging


def _get_verbose_level(args):
    if args.verbose is True:
        return logging.DEBUG
    elif args.quiet is True:
        return logging.ERROR
    else:
        return logging.INFO


class CustomizedFormatter(logging.Formatter):

    NO_COLOR = '\033[0m'
    COLOR_BLUE = '\033[94m'
    COLOR_RED = '\033[91m'
    COLOR_GREEN = '\033[92m'

    FORMATS = {
        logging.INFO:
        f"%(asctime)s - {COLOR_BLUE}| %(levelname)s  |{NO_COLOR} - %(message)s",
        logging.DEBUG:
        f"%(asctime)s - {COLOR_GREEN}| %(levelname)s |{NO_COLOR} - %(message)s\
        (%(filename)s:%(lineno)d)",
        logging.ERROR:
        f"%(asctime)s - {COLOR_RED}| %(levelname)s |{NO_COLOR} - %(message)s \
        (%(filename)s:%(lineno)d)"
    }

    # Required to override logging.Formatter.format
    def format(self, record):
        required_format = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(required_format)
        return formatter.format(record)


def configure_logger(args, name: str):
    verbosity = _get_verbose_level(args)
    logging.basicConfig(
        filename=name,
        level=verbosity,
        format='%(asctime)s %(levelname)s %(message)s',
    )

    logger = logging.getLogger('')
    output_stream = logging.StreamHandler()
    output_stream.setLevel(verbosity)
    output_stream.setFormatter(CustomizedFormatter())
    logger.addHandler(output_stream)
