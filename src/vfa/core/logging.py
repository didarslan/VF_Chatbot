from __future__ import annotations

import logging

def get_logger(name: str = "vfa") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        h = logging.StreamHandler()
        fmt = logging.Formatter("[%(levelname)s] %(asctime)s %(name)s - %(message)s")
        h.setFormatter(fmt)
        logger.addHandler(h)
    return logger
