import os
import shutil
from typing import Iterable


def delete_file(file: str) -> None:
    try:
        os.remove(file)
    except FileNotFoundError:
        pass


def delete_folder(path: str) -> None:
    shutil.rmtree(path, ignore_errors=True)


def delete_folders(folders: Iterable[str]) -> None:
    for folder in folders:
        shutil.rmtree(folder, ignore_errors=True)


def copy_file(source: str, destination: str) -> None:
    shutil.copy(source, destination)


def copy_folder(source: str, destination: str) -> None:
    shutil.copytree(source, destination)
