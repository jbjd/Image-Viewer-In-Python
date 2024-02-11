"""
Code for OS specific stuff
"""

from collections.abc import Iterator
from os import name, scandir
from re import sub

if name == "nt":
    from ctypes import windll

    illegal_char = r'[<>:"|?*]'

    def OS_name_cmp(a: str, b: str) -> bool:
        return windll.shlwapi.StrCmpLogicalW(a, b) < 0

else:  # linux / can't determine / unsupported OS
    illegal_char = r"[]"

    def OS_name_cmp(a: str, b: str) -> bool:
        return a < b


def clean_str_for_OS_path(file_name: str) -> str:
    """Removes characters that file names can't have on this OS"""
    return sub(illegal_char, "", file_name)


def walk_dir(directory_path: str) -> Iterator[str]:
    """Copied from OS module and edited to yield each file
    and only files instead of including dirs/extra info"""

    with scandir(directory_path) as scandir_iter:
        while True:
            try:
                entry = next(scandir_iter)
            except (StopIteration, OSError):
                return

            try:
                is_dir = entry.is_dir()
            except OSError:
                is_dir = False

            if not is_dir:
                yield entry.name
