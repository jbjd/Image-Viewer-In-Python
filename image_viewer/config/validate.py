"""
Validation of user inputted config values
"""

import re


def validate_or_default(keybind: str, default: str) -> str:
    """Given a tkinter keybind, validate if its allowed
    and return keybind if its valid or the default if its not"""
    f_key_re = r"F([1-9]|10|11|12)"
    control_key_re = r"Control-[a-zA-Z0-9]"

    match = re.match(f"^<(({f_key_re})|({control_key_re}))>$", keybind)

    return default if match is None else keybind
