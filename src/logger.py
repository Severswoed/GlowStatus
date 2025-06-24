import logging

def get_logger(name="GlowStatus"):
    logger = logging.getLogger(name)
    if not logger.handlers:  # Only add handler if none exist for this logger
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger