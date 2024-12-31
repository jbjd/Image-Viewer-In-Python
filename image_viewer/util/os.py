"""
Code for OS specific stuff
"""

import os
from collections.abc import Iterator
from re import Pattern
from re import compile as re_compile
from typing import Final

illegal_char: Pattern[str]
kb_size: int
if os.name == "nt":
    import ctypes
    from ctypes import windll  # type: ignore

    from send2trash.win.legacy import send2trash
    from winshell import undelete, x_winshell

    illegal_char = re_compile(r'[<>:"|?*]')
    kb_size = 1024

    class OPENASINFO(ctypes.Structure):
        _fields_ = [
            ("pcszFile", ctypes.c_wchar_p),
            ("pcszClass", ctypes.c_wchar_p),
            ("oaifInFlags", ctypes.c_int32),
        ]

    def OS_name_cmp(a: str, b: str) -> bool:
        return windll.shlwapi.StrCmpLogicalW(a, b) < 0

    def restore_from_bin(original_path: str) -> None:
        try:
            undelete(original_path)
        except x_winshell as e:
            raise OSError from e  # change error type so catching is not OS specific

else:  # assume linux for now
    import subprocess
    from glob import glob
    from tkinter.messagebox import showinfo

    from send2trash import send2trash
    from send2trash.plat_other import HOMETRASH

    illegal_char = re_compile("")
    kb_size = 1000

    def OS_name_cmp(a: str, b: str) -> bool:
        return a < b

    def restore_from_bin(original_path: str) -> None:
        name_start: int = original_path.rfind("/")
        file_name_and_suffix: str = (
            original_path if name_start == -1 else original_path[name_start + 1 :]
        )
        suffix_start: int = file_name_and_suffix.rfind(".")
        if suffix_start == -1:
            file_name = file_name_and_suffix
            suffix = ""
        else:
            file_name = file_name_and_suffix[:suffix_start]
            suffix = file_name_and_suffix[suffix_start:]

        # Files with same name will be test.png.trashinfo, test.2.png.trashinfo
        info_paths: list[str] = glob(f"{HOMETRASH}/info/{file_name}*{suffix}.trashinfo")
        for info_path in info_paths:
            with open(info_path, "r", encoding="utf-8") as fp:
                line: str
                while line := fp.readline().strip():
                    if line.startswith("Path="):
                        break
                else:
                    return  # no line with Path= was found
                deleted_file_original_path: str = line.strip().replace("Path=", "", 1)
                if deleted_file_original_path == original_path:
                    deleted_file_name = info_path[info_path.rfind("/info/") + 6 : -10]
                    path_to_trashed_file: str = f"{HOMETRASH}/files/{deleted_file_name}"

                    # trashinfo file may exist, but actual file does not
                    if os.path.exists(path_to_trashed_file):
                        os.rename(path_to_trashed_file, original_path)
                        os.remove(info_path)
                        break


def open_with(hwnd: int, file: str) -> None:
    if os.name != "nt":
        raise NotImplementedError

    OAIF_EXEC: Final[int] = 0x04
    OAIF_HIDE_REGISTRATION: Final[int] = 0x20
    open_as_info = OPENASINFO(
        pcszFile=file,
        pcszClass=None,
        oaifInFlags=OAIF_EXEC | OAIF_HIDE_REGISTRATION,
    )

    windll.shell32.SHOpenWithDialog(hwnd, open_as_info)


def show_info_popup(hwnd: int, title: str, body: str) -> None:
    if os.name == "nt":
        windll.user32.MessageBoxW(hwnd, body, title, 0)
    else:
        showinfo(title, body)


def clean_str_for_OS_path(path: str) -> str:
    """Removes characters that paths on this OS can't have"""
    return illegal_char.sub("", path)


def get_byte_display(size_in_bytes: int) -> str:
    """Given bytes, formats it into a string using kb or mb"""
    size_in_kb: int = size_in_bytes // kb_size
    return f"{size_in_kb/kb_size:.2f}mb" if size_in_kb > 999 else f"{size_in_kb}kb"


def trash_file(path: str) -> None:
    """OS generic way to send files to trash"""
    send2trash(path)


def get_normalized_dir_name(path: str) -> str:
    """Gets directory name of a file path and normalizes it"""
    dir_name: str = os.path.dirname(path)
    # normpath of empty string returns "."
    return os.path.normpath(dir_name) if dir_name != "" else ""


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
