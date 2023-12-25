import os
from re import sub

from util.image import ImagePath

if os.name == "nt":
    from ctypes import windll

    illegal_char = r'[\\/<>:"|?*]'

    def OS_name_cmp(a: str, b: str) -> bool:
        return windll.shlwapi.StrCmpLogicalW(a, b) < 0

else:  # if can't determine / unsupported OS
    illegal_char = r"[/]"

    def OS_name_cmp(a: str, b: str) -> bool:
        return a < b


def clean_str_for_OS_path(name: str) -> str:
    return sub(illegal_char, "", name)


class OSFileSortKey:
    """Key for sorting files the same way the current OS does"""

    __slots__ = "name"

    def __init__(self, image: ImagePath) -> None:
        self.name: str = image.name

    def __lt__(self, other: ImagePath) -> bool:
        return OS_name_cmp(self.name, other.name)
