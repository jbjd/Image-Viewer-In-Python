import os
import shutil
from glob import glob
from typing import Iterable


def delete_file_globs(glob_patterns: Iterable[str]) -> None:
    for glob_pattern in glob_patterns:
        for file in glob(glob_pattern, recursive=True):
            os.remove(file)

            dir: str = os.path.dirname(file)
            if not os.listdir(dir):
                os.rmdir(dir)


def delete_folder(path: str) -> None:
    shutil.rmtree(path, ignore_errors=True)


def delete_folders(folders: Iterable[str]) -> None:
    for folder in folders:
        shutil.rmtree(folder, ignore_errors=True)


def copy_file(source: str, destination: str) -> None:
    shutil.copy(source, destination)


def copy_folder(source: str, destination: str) -> None:
    shutil.copytree(source, destination)
