from functools import wraps
import time


def catch_exception(*exceptions):
    def run_func(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                return e

        return wrapper

    return run_func
