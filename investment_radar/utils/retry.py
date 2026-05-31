import time
from functools import wraps

import requests


def retry_on_exception(max_attempts: int = 3, backoff_seconds: float = 0.8, exceptions=(requests.RequestException,)):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as error:
                    last_error = error
                    if attempt == max_attempts:
                        break
                    time.sleep(backoff_seconds * attempt)
            raise last_error

        return wrapper

    return decorator
