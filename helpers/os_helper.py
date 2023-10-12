import os

if os.name == "nt":
    from ctypes import windll

    def get_illegal_OS_char_re():
        return r'[\\\\/<>:"|?*]'

    def OS_name_cmp(a, b) -> bool:
        return windll.shlwapi.StrCmpLogicalW(a, b) < 0

else:
    # if can't determine OS
    def get_illegal_OS_char_re():
        return r"[/]"

    def OS_name_cmp(a, b) -> bool:
        return a < b


# used to sort files same as current OS
class OSFileSortKey:
    __slots__ = "name"

    def __init__(self, image) -> None:
        self.name: str = image.name

    def __lt__(self, b) -> bool:
        return OS_name_cmp(self.name, b.name)
