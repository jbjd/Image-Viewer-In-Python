import os
from re import sub

if os.name == "nt":
    from ctypes import windll

    illegal_char = r'[\\/<>:"|?*]'

    def OS_name_cmp(a: str, b: str) -> bool:
        return windll.shlwapi.StrCmpLogicalW(a, b) < 0

else:  # linux / can't determine / unsupported OS
    illegal_char = r"[/]"

    def OS_name_cmp(a: str, b: str) -> bool:
        return a < b


def clean_str_for_OS_path(name: str) -> str:
    return sub(illegal_char, "", name)
