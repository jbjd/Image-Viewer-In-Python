import os

if os.name == "nt":
    from ctypes import windll

    illegal_char = r'[\\\\/<>:"|?*]'

    def OS_name_cmp(a, b) -> bool:
        return windll.shlwapi.StrCmpLogicalW(a, b) < 0

else:
    # if can't determine OS
    illegal_char = r"[/]"

    def OS_name_cmp(a, b) -> bool:
        return a < b


def get_illegal_OS_char_re():
    return illegal_char


# used to sort files same as current OS
class OSFileSortKey:
    __slots__ = "name"

    def __init__(self, image) -> None:
        self.name: str = image.name

    def __lt__(self, b) -> bool:
        return OS_name_cmp(self.name, b.name)
