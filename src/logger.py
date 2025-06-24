import logging

def get_logger(name="GlowStatus"):
    logger = logging.getLogger(name)
    logger.propagate = False  # Prevent double logging via parent/root logger

    # Remove all handlers before adding one (guaranteed single handler)
    while logger.handlers:
        logger.removeHandler(logger.handlers[0])

    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger