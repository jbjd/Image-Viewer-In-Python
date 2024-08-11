import os
import re
import shutil
from glob import glob
from typing import Iterable

from compile_utils.regex import RegexReplacement


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


def regex_replace(
    path: str, regex_replacements: RegexReplacement | Iterable[RegexReplacement]
) -> None:
    with open(path) as fp:
        contents = fp.read()

    if isinstance(regex_replacements, RegexReplacement):
        regex_replacements = [regex_replacements]

    regex_replacement: RegexReplacement
    for regex_replacement in regex_replacements:
        contents = re.sub(
            regex_replacement.pattern,
            regex_replacement.replacement,
            contents,
            count=regex_replacement.count,
            flags=regex_replacement.flags,
        )

    with open(path, "w") as fp:
        fp.write(contents)
