import os
import re
import shutil
from glob import glob
from typing import Iterable


def delete_file_globs(glob_patterns: Iterable[str]) -> None:
    for glob_pattern in glob_patterns:
        for file in glob(glob_pattern, recursive=True):
            os.remove(file)


def delete_folder(path: str) -> None:
    shutil.rmtree(path, ignore_errors=True)


def delete_folders(folders: Iterable[str]) -> None:
    for folder in folders:
        shutil.rmtree(folder, ignore_errors=True)


def copy_folder(source: str, destination: str) -> None:
    shutil.copy(source, destination)


def regex_replace(path: str, pattern: str, replacement: str, flags=0) -> None:
    with open(path) as fp:
        contents = fp.read()

    contents = re.sub(pattern, replacement, contents, flags=flags)

    with open(path, "w") as fp:
        fp.write(contents)
