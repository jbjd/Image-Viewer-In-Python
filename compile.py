import os
import platform
from argparse import Namespace
from glob import glob
from importlib import import_module
from subprocess import Popen
from typing import Final

from compile_utils.args import CompileArgumentParser
from compile_utils.cleaner import (
    clean_file_and_copy,
    clean_tk_files,
    move_files_to_tmp_and_clean,
)
from compile_utils.file_operations import (
    copy_file,
    copy_folder,
    delete_file_globs,
    delete_folder,
    delete_folders,
)
from compile_utils.nuitka import start_nuitka_compilation
from compile_utils.validation import raise_if_unsupported_python_version

raise_if_unsupported_python_version()

WORKING_DIR: Final[str] = os.path.abspath(os.path.dirname(__file__))
FILE: Final[str] = "__main__"
TMP_DIR: Final[str] = os.path.join(WORKING_DIR, "tmp")
CODE_DIR: Final[str] = os.path.join(WORKING_DIR, "image_viewer")
COMPILE_DIR: Final[str] = os.path.join(WORKING_DIR, f"{FILE}.dist")
BUILD_DIR: Final[str] = os.path.join(WORKING_DIR, f"{FILE}.build")
EXECUTABLE_EXT: Final[str] = ".exe" if os.name == "nt" else ".bin"
EXECUTABLE_NAME: Final[str] = f"viewer{EXECUTABLE_EXT}"
DEFAULT_INSTALL_PATH: str
DATA_FILE_PATHS: list[str]

if os.name == "nt":
    dll_suffix: str
    folder_suffix: str
    if platform.architecture()[0] == "32bit":
        dll_suffix = "_x86"
        folder_suffix = " (x86)"
    else:
        dll_suffix = folder_suffix = ""

    DEFAULT_INSTALL_PATH = f"C:/Program Files{folder_suffix}/Personal Image Viewer/"
    DATA_FILE_PATHS = ["icon/icon.ico", f"dll/libturbojpeg{dll_suffix}.dll"]
else:
    DEFAULT_INSTALL_PATH = "/usr/local/personal-image-viewer/"
    DATA_FILE_PATHS = ["icon/icon.png"]

DATA_FILE_PATHS.append("config.ini")

parser = CompileArgumentParser(DEFAULT_INSTALL_PATH)

with open(os.path.join(WORKING_DIR, "skippable_imports.txt"), "r") as fp:
    imports_to_skip: list[str] = fp.read().strip().split("\n")

args: Namespace
nuitka_args: list[str]
args, nuitka_args = parser.parse_known_args(imports_to_skip)
is_standalone = "--standalone" in nuitka_args

if os.name == "nt":
    windows_icon_file_path: str = f"{CODE_DIR}/icon/icon.ico"
    nuitka_args.append(f"--windows-icon-from-ico={windows_icon_file_path}")

# Before compiling, copy to tmp dir and remove type-hints/clean code
# I thought nuitka would handle this, but I guess not?
delete_folder(TMP_DIR)
try:
    # use "" as module for image_viewer should it should be considered root
    move_files_to_tmp_and_clean(CODE_DIR, TMP_DIR, "")

    for mod_name in ["turbojpeg", "send2trash", "PIL", "numpy"]:
        modules_to_skip: set[str] = set(
            i for i in imports_to_skip if i.startswith(mod_name)
        )

        module = import_module(mod_name)
        if module.__file__ is None:
            print(f"Error getting module {mod_name}'s filepath")
            continue
        base_file_name: str = os.path.basename(module.__file__)
        if mod_name == "numpy":
            site_packages_path: str = os.path.dirname(os.path.dirname(module.__file__))
            lib_path: str = os.path.join(site_packages_path, "numpy.libs")
            copy_folder(lib_path, os.path.join(TMP_DIR, "numpy.libs"))
        if base_file_name == "__init__.py":
            # its really a folder
            move_files_to_tmp_and_clean(
                os.path.dirname(module.__file__), TMP_DIR, mod_name, modules_to_skip
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

    delete_folder(COMPILE_DIR)
    input_file: str = f"{TMP_DIR}/{FILE}.py"
    process: Popen = start_nuitka_compilation(
        args.python_path, input_file, WORKING_DIR, nuitka_args
    )

    install_path: str = args.install_path if not args.debug else COMPILE_DIR
    os.makedirs(install_path, exist_ok=True)

    print("Waiting for nuitka compilation...")

    if process.wait():
        exit(1)

    for data_file_path in DATA_FILE_PATHS:
        old_path = os.path.join(CODE_DIR, data_file_path)
        new_path = os.path.join(COMPILE_DIR, data_file_path)
        os.makedirs(os.path.dirname(new_path), exist_ok=True)
        copy_file(old_path, new_path)

    if is_standalone:
        clean_tk_files(COMPILE_DIR)
    else:
        # nuitka puts exe outside of dist when not standalone
        os.rename(
            os.path.join(WORKING_DIR, EXECUTABLE_NAME),
            os.path.join(COMPILE_DIR, EXECUTABLE_NAME),
        )

    if not args.debug:
        delete_folder(install_path)
        os.rename(COMPILE_DIR, install_path)
finally:
    if not args.debug and not args.no_cleanup:
        delete_folders([BUILD_DIR, COMPILE_DIR, TMP_DIR])
        delete_file_globs([os.path.join(WORKING_DIR, f"{FILE}.cmd")])

print("\nFinished")
print("Installed to", install_path)

path_to_check: str = install_path
install_byte_size: int = sum(
    os.stat(p).st_size
    for p in glob(f"{path_to_check}/**/*", recursive=True)
    if os.path.isfile(p)
)
print(f"Install Size: {install_byte_size:,} bytes")
