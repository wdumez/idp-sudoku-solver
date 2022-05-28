"""Utility functions for Sudoku solving."""
from functools import wraps
import logging
from time import time


def log_time(func):
    """Decorator that logs function call time when debugging."""
    @wraps(func)
    def wrap(*args, **kwargs):
        start = time()
        value = func(*args, **kwargs)
        delta = time() - start
        msg = f'{func.__name__} took {delta:.3f} seconds.'
        if __debug__:
            logging.debug(msg)
        return value
    return wrap
