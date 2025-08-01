"""
Code for OS specific stuff
"""

import os
import sys
from collections.abc import Iterator
from typing import Final

if os.name == "nt":
    from ctypes import windll  # type: ignore

    from util._os_nt import get_files_in_folder as _get_files_in_folder
    from util._os_nt import restore_file as _restore_file
    from util._os_nt import trash_file as _trash_file

    def OS_name_cmp(a: str, b: str) -> bool:
        return windll.shlwapi.StrCmpLogicalW(a, b) < 0

    def get_files_in_folder(directory_path: str) -> Iterator[str]:
        files: list[str] = _get_files_in_folder(directory_path)
        return iter(files)

else:  # assume linux for now
    from glob import glob
    from tkinter.messagebox import showinfo

    from send2trash.plat_other import HOMETRASH, send2trash

    def OS_name_cmp(a: str, b: str) -> bool:
        return a < b

    # TODO: break this function into smaller bits
    def _restore_file(original_path: str) -> None:
        name_start: int = original_path.rfind("/")
        name_and_suffix: str = (
            original_path if name_start == -1 else original_path[name_start + 1 :]
        )
        file_name, file_suffix = split_name_and_suffix(name_and_suffix)

        # Files with same name will be test.png.trashinfo, test.2.png.trashinfo
        # or 'test 2.png.trashinfo'
        info_paths: list[str] = glob(
            f"{HOMETRASH}/info/{file_name}*{file_suffix}.trashinfo"
        )
        for info_path in info_paths:
            with open(info_path, "r", encoding="utf-8") as fp:
                line: str
                while line := fp.readline().strip():  # TODO: use configparser instead
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

    def get_files_in_folder(directory_path: str) -> Iterator[str]:
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


def show_info_popup(hwnd: int, title: str, body: str) -> None:
    """If on Windows, shows info popup as child of parent
    Otherwise shows parent-less info popup"""
    if os.name == "nt":
        windll.user32.MessageBoxW(hwnd, body, title, 0)
    else:
        showinfo(title, body)


def get_byte_display(size_in_bytes: int) -> str:
    """Given bytes, formats it into a string using kb or mb"""
    kb_size: int = 1024 if os.name == "nt" else 1000
    size_in_kb: int = size_in_bytes // kb_size
    return f"{size_in_kb/kb_size:.2f}mb" if size_in_kb > 999 else f"{size_in_kb}kb"


def trash_file(path: str) -> None:
    """OS generic way to send files to trash"""
    if os.name == "nt":
        _trash_file(0, path)
    else:
        send2trash(path)


def restore_file(path: str) -> None:
    """OS Generic way to restore a file from trash"""
    if os.name == "nt":
        _restore_file(0, path)
    else:
        _restore_file(path)


def get_normalized_dir_name(path: str) -> str:
    """Gets directory name of a file path and normalizes it"""
    dir_name: str = os.path.dirname(path)
    # normpath of empty string returns "."
    return os.path.normpath(dir_name) if dir_name != "" else ""


def maybe_truncate_long_name(name_and_suffix: str) -> str:
    """Takes a file name and returns a shortened version if its too long"""
    name, suffix = split_name_and_suffix(name_and_suffix)

    MAX: Final[int] = 40
    if len(name) <= MAX:
        return name_and_suffix

    return f"{name[:MAX]}(…){suffix}"


def split_name_and_suffix(name_and_suffix: str) -> tuple[str, str]:
    """Given a file name, return the name without the suffix
    and the suffix separately"""
    suffix_start: int = name_and_suffix.rfind(".")
    if suffix_start == -1:
        file_name = name_and_suffix
        suffix = ""
    else:
        file_name = name_and_suffix[:suffix_start]
        suffix = name_and_suffix[suffix_start:]

    return file_name, suffix


def get_path_to_exe_folder() -> str:
    """Returns path to folder containing exe/py file
    of running program"""
    return os.path.dirname(sys.argv[0])
