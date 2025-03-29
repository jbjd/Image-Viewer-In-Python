"""Utilities for exception handling in tests"""

from functools import wraps
from typing import Callable


def safe_wrapper(function: Callable[..., None]):
    """Given a callable, pass if Exception is raised"""

    @wraps(function)
    def wrapper(*args, **kwargs) -> None:
        try:
            function(*args, **kwargs)
        except Exception:
            pass

    return wrapper
