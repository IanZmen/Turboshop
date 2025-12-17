import logging

def get_logger(name: str = "etl") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        log_formatter = logging.Formatter("[%(levelname)s] %(message)s")
        handler.setFormatter(log_formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
