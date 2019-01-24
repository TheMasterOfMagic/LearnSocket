import logging

logger_name = 'example'
logger = logging.getLogger(logger_name)
logger.setLevel(logging.DEBUG)

# create file handler
fh = logging.StreamHandler()
fh.setLevel(logging.DEBUG)

# create formatter
fmt = '[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s'
date_fmt = '%m-%d %H:%M:%S'
formatter = logging.Formatter(fmt, date_fmt)

# add handler and formatter to logger
fh.setFormatter(formatter)
logger.addHandler(fh)

debug, info, warn, error, critical = logger.debug, logger.info, logger.warning, logger.error, logger.critical

__all__ = 'debug', 'info', 'warn', 'error', 'critical'
