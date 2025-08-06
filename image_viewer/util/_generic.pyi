"""Utility functions that aren't better classified in other files"""

def is_valid_hex_color(hex_color: str) -> bool:
    """Given a hex color string in format #123456, return True if it is valid"""

def is_valid_keybind(keybind: str) -> bool:
    """Given a keybind, returns True if it matches one of the following formats
    <F[0-9]> <F1[0-2]> <Control-[a-zA-Z0-9]>"""
