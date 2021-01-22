import logging


class Logger():

    def __init__(self, logpath=None, level=logging.DEBUG):
        # Gets or creates a logger
        logger = logging.getLogger(__name__)

        # set log level
        logger.setLevel(level)

        formatter = logging.Formatter(
            '%(asctime)s : %(levelname)s : %(message)s')

        handler = None
        if not logger.handlers:
            if logpath is not None:
                # setup logging to file
                handler = logging.FileHandler(logpath)
                handler.setFormatter(formatter)
                logger.addHandler(handler)
            else:
                # setup logging to stdout stream
                handler = logging.StreamHandler()
                handler.setFormatter(formatter)
                logger.addHandler(handler)

        self.logger = logger

    def debug(self, msg, extra=None):
        self.logger.debug(msg, extra=extra)

    def info(self, msg, extra=None):
        self.logger.info(msg, extra=extra)

    def warning(self, msg, extra=None):
        self.logger.warn(msg, extra=extra)

    def error(self, msg, extra=None):
        self.logger.error(msg, extra=extra)

    def critical(self, msg, extra=None):
        self.logger.critical(msg, extra=extra)
