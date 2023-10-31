import os
from re import sub

from image import ImagePath

if os.name == "nt":
    from ctypes import windll

    illegal_char = r'[\\/<>:"|?*]'

    def OS_name_cmp(a, b) -> bool:
        return windll.shlwapi.StrCmpLogicalW(a, b) < 0

else:
    # if can't determine OS
    illegal_char = r"[/]"

    def OS_name_cmp(a, b) -> bool:
        return a < b


def clean_str_for_OS_path(name: str) -> str:
    return sub(illegal_char, "", name)


# used to sort files the same as current OS does
class OSFileSortKey:
    __slots__ = "name"

    def __init__(self, image: ImagePath) -> None:
        self.name: str = image.name

    def __lt__(self, other: ImagePath) -> bool:
        return OS_name_cmp(self.name, other.name)
