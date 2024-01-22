import os
from collections.abc import Iterator
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


def walk_dir(directory_path: str) -> Iterator[str]:
    """Copied from OS module and edited to yield each file
    and only files instead of including dirs/extra info"""

    scandir_iter = os.scandir(directory_path)

    with scandir_iter:
        while True:
            try:
                entry = next(scandir_iter)
            except Exception:
                return

            try:
                is_dir = entry.is_dir()
            except OSError:
                is_dir = False

            if not is_dir:
                yield entry.name
