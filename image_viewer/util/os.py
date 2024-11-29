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
    import subprocess
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

        # mv f"{HOMETRASH}/files/{name}" original_path
        find_result = subprocess.run(
            f"find {HOMETRASH}/info/{file_name}*{suffix}.trashinfo",
            stdout=subprocess.PIPE,
            shell=True,
        )
        if find_result.returncode != 0:
            return

        output: str = find_result.stdout.decode("utf-8")
        info_paths = output.strip().split("\n")
        for info_path in info_paths:
            with open(info_path, "r", encoding="utf-8") as fp:
                _ = fp.readline()
                deleted_files_original_path: str = (
                    fp.readline().strip().replace("Path=", "", 1)
                )
                if deleted_files_original_path == original_path:
                    deleted_file_name = info_path[info_path.rfind("/info/") + 6 : -10]
                    path_to_trashed_file: str = f"{HOMETRASH}/files/{deleted_file_name}"
                    # to_restore_path: str = info_path.replace(
                    #     f"/info/{file_name}", f"/files/{file_name}"
                    # )
                    break


def show_info_popup(title: str, body: str) -> None:
    if os.name == "nt":
        windll.user32.MessageBoxW(0, body, title, 0)
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


restore_from_bin("/home/jbjd/Pictures/test2.png")
