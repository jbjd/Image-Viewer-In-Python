"""
Code for OS specific stuff
"""

import os
from collections.abc import Iterator
from re import Pattern
from re import compile as re_compile

illegal_char: Pattern[str]
kb_size: int
if os.name == "nt":
    from ctypes import windll  # type: ignore

    from send2trash.win.legacy import send2trash
    from winshell import undelete, x_winshell

    illegal_char = re_compile(r'[<>:"|?*]')
    kb_size = 1024

    def OS_name_cmp(a: str, b: str) -> bool:
        return windll.shlwapi.StrCmpLogicalW(a, b) < 0

    def restore_from_bin(original_path: str) -> None:
        try:
            undelete(os.path.normpath(original_path))
        except x_winshell as e:
            raise OSError from e  # change error type so catching is not OS specific

else:  # assume linux for now
    from send2trash import send2trash

    illegal_char = re_compile("")
    kb_size = 1000

    def OS_name_cmp(a: str, b: str) -> bool:
        return a < b

    def restore_from_bin(original_path: str) -> None:
        raise NotImplementedError  # TODO: add option for linux


def clean_str_for_OS_path(path: str) -> str:
    """Removes characters that paths on this OS can't have"""
    return illegal_char.sub("", path)


def get_byte_display(size_in_bytes: int) -> str:
    """Given bytes, formats it into a string using kb or mb"""
    size_in_kb: int = size_in_bytes // kb_size
    return f"{size_in_kb/kb_size:.2f}mb" if size_in_kb > 999 else f"{size_in_kb}kb"


def trash_file(path: str) -> None:
    """OS generic way to send files to trash"""
    send2trash(os.path.normpath(path))


def get_dir_name(path: str) -> str:
    """Gets dir name of a file path and normalizes it"""
    path_dir: str = os.path.dirname(path)
    return os.path.normpath(path_dir) if path_dir != "" else ""


def walk_dir(directory_path: str) -> Iterator[str]:
    """Copied from OS module and edited to yield each file
    and only files instead of including dirs/extra info"""

    with os.scandir(directory_path) as scandir_iter:
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
