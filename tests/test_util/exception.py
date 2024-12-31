from functools import wraps
from typing import Callable


def safe_wrapper(function: Callable[..., None]):
    @wraps(function)
    def wrapper(*args, **kwargs) -> None:
        try:
            return function(*args, **kwargs)
        except Exception:
            pass

    return wrapper
