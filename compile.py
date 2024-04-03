import os
import shutil
from argparse import Namespace
from importlib import import_module
from subprocess import Popen
from typing import Final

from compile_utils.args import CompileArgumentParser
from compile_utils.cleaner import clean_file_and_copy, move_files_to_tmp_and_clean
from compile_utils.nuitka import start_nuitka_compilation
from compile_utils.validation import raise_if_unsupported_python_version

raise_if_unsupported_python_version()

WORKING_DIR: Final[str] = os.path.abspath(os.path.dirname(__file__))
FILE: Final[str] = "__main__"
TMP_DIR: Final[str] = os.path.join(WORKING_DIR, "tmp")
CODE_DIR: Final[str] = os.path.join(WORKING_DIR, "image_viewer")
COMPILE_DIR: Final[str] = os.path.join(WORKING_DIR, f"{FILE}.dist")
BUILD_DIR: Final[str] = os.path.join(WORKING_DIR, f"{FILE}.build")
DEFAULT_INSTALL_PATH: str
DATA_FILE_PATHS: list[str]

if os.name == "nt":
    DEFAULT_INSTALL_PATH = "C:/Program Files/Personal Image Viewer/"
    DATA_FILE_PATHS = ["icon/icon.ico", "dll/libturbojpeg.dll"]
else:
    DEFAULT_INSTALL_PATH = "/usr/local/personal-image-viewer/"
    DATA_FILE_PATHS = ["icon/icon.png"]

parser = CompileArgumentParser(DEFAULT_INSTALL_PATH)

args: Namespace
nuitka_args: list[str]
args, nuitka_args = parser.parse_known_args(WORKING_DIR)

if os.name == "nt":
    windows_icon_file_path: str = f"{CODE_DIR}/icon/icon.ico"
    nuitka_args.append(f"--windows-icon-from-ico={windows_icon_file_path}")

# Before compiling, copy to tmp dir and remove type-hints/clean code
# I thought nuitka would handle this, but I guess not?
shutil.rmtree(TMP_DIR, ignore_errors=True)
try:
    # use "" as module for image_viewer should it should be considered root
    move_files_to_tmp_and_clean(CODE_DIR, TMP_DIR, "")

    for mod_name in ["turbojpeg", "send2trash", "PIL"]:  # TODO: consider adding numpy
        module = import_module(mod_name)
        if module.__file__ is None:
            print(f"Error getting module {mod_name}'s filepath")
            continue
        base_file_name: str = os.path.basename(module.__file__)
        if base_file_name == "__init__.py":
            # its really a folder
            move_files_to_tmp_and_clean(
                os.path.dirname(module.__file__), TMP_DIR, mod_name
            )
        else:
            # its just one file
            clean_file_and_copy(
                module.__file__,
                os.path.join(TMP_DIR, base_file_name),
                mod_name,
            )

    if args.skip_nuitka:
        exit(0)

    input_file: str = f"{TMP_DIR}/{FILE}.py"
    process: Popen = start_nuitka_compilation(
        args.python_path, input_file, WORKING_DIR, nuitka_args
    )

    install_path: str = args.install_path
    os.makedirs(install_path, exist_ok=True)

    print("Waiting for nuitka compilation...")

    if process.wait():
        exit(1)

    for data_file_path in DATA_FILE_PATHS:
        old_path = os.path.join(CODE_DIR, data_file_path)
        new_path = os.path.join(COMPILE_DIR, data_file_path)
        os.makedirs(os.path.dirname(new_path), exist_ok=True)
        shutil.copy(old_path, new_path)

    if args.debug:
        exit(0)

    shutil.rmtree(install_path, ignore_errors=True)
    os.rename(COMPILE_DIR, install_path)
finally:
    if not args.debug:
        shutil.rmtree(BUILD_DIR, ignore_errors=True)
        shutil.rmtree(COMPILE_DIR, ignore_errors=True)
        if not args.skip_nuitka:
            shutil.rmtree(TMP_DIR, ignore_errors=True)
        try:
            os.remove(os.path.join(WORKING_DIR, f"{FILE}.cmd"))
        except FileNotFoundError:
            pass

print("\nFinished")
print("Installed to", install_path)
