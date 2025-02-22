import logging
logger = logging.getLogger(__name__)

def enable_logging():
    logging.basicConfig(level = logging.DEBUG,
                        format = '%(asctime)s-%(levelname)s-%(threadName)s-%(name)s-%(lineno)d-%(funcName)s-%(message)s',
                        datefmt = '%Y%m%d-%H:%M:%S')
    logger.debug("logging level >= 'DEBUG' to stdout")

from .mqtt import MQTTClient