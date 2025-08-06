"""A script to compile the image viewer into an executable file via nuitka"""

import os
import sys
from argparse import Namespace
from importlib import import_module
from importlib.metadata import version as get_module_version
from subprocess import Popen
from typing import Final

from personal_compile_tools.file_operations import (
    copy_file,
    copy_folder,
    delete_file,
    delete_folder,
    delete_folders,
    get_folder_size,
)

from compile_utils.args import CompileArgumentParser, NuitkaArgs
from compile_utils.cleaner import (
    clean_file_and_copy,
    clean_tk_files,
    move_files_to_tmp_and_clean,
    strip_files,
    warn_unused_code_skips,
)
from compile_utils.constants import BUILD_INFO_FILE
from compile_utils.module_dependencies import (
    get_normalized_module_name,
    module_dependencies,
    modules_to_skip,
)
from compile_utils.nuitka_ext import start_nuitka_compilation
from compile_utils.package_info import IMAGE_VIEWER_NAME
from compile_utils.validation import (
    validate_module_requirements,
    validate_python_version,
)

validate_python_version()

WORKING_DIR: Final[str] = os.path.normpath(os.path.dirname(__file__))
FILE: Final[str] = "__main__"
TMP_DIR: Final[str] = os.path.join(WORKING_DIR, "tmp")
CODE_DIR: Final[str] = os.path.join(WORKING_DIR, "image_viewer")
COMPILE_DIR: Final[str] = os.path.join(WORKING_DIR, f"{FILE}.dist")
BUILD_DIR: Final[str] = os.path.join(WORKING_DIR, f"{FILE}.build")
EXECUTABLE_EXT: Final[str] = "exe" if os.name == "nt" else "bin"
EXECUTABLE_NAME: Final[str] = f"viewer.{EXECUTABLE_EXT}"
DEFAULT_INSTALL_PATH: str
DATA_FILE_PATHS: list[str] = ["config.ini"]

if os.name == "nt":
    DEFAULT_INSTALL_PATH = "C:/Program Files/Personal Image Viewer/"
    DATA_FILE_PATHS = ["icon/icon.ico", "dll/libturbojpeg.dll"]
else:
    DEFAULT_INSTALL_PATH = "/usr/local/personal-image-viewer/"
    DATA_FILE_PATHS = ["icon/icon.png"]

parser = CompileArgumentParser(DEFAULT_INSTALL_PATH)

args: Namespace
nuitka_args: list[str]
args, nuitka_args = parser.parse_known_args(modules_to_skip)
is_standalone = NuitkaArgs.STANDALONE in nuitka_args

if os.name == "nt":
    nuitka_args += [
        NuitkaArgs.MINGW64,
        NuitkaArgs.WINDOWS_ICON_FROM_ICO.with_value(f"{CODE_DIR}/icon/icon.ico"),
    ]

validate_module_requirements(is_standalone)

# Before compiling, copy to tmp dir and remove type-hints/clean code
# I thought nuitka would handle this, but I guess not?
delete_folder(TMP_DIR)
try:
    # use "" as module for image_viewer, it should be considered root
    move_files_to_tmp_and_clean(CODE_DIR, TMP_DIR, IMAGE_VIEWER_NAME)

    for module in module_dependencies:
        module_name: str = get_normalized_module_name(module)
        sub_modules_to_skip: set[str] = set(
            i for i in modules_to_skip if i.startswith(module_name)
        )

        module = import_module(module_name)
        if module.__file__ is None:
            print(f"Error getting module {module_name}'s filepath")
            continue
        base_file_name: str = os.path.basename(module.__file__)
        if module_name == "numpy":
            site_packages_path: str = os.path.dirname(os.path.dirname(module.__file__))
            lib_path: str = os.path.join(site_packages_path, "numpy.libs")
            copy_folder(lib_path, os.path.join(TMP_DIR, "numpy.libs"))
        elif module_name == "PIL" and os.name == "posix":
            site_packages_path = os.path.dirname(os.path.dirname(module.__file__))
            lib_path = os.path.join(site_packages_path, "pillow.libs")
            copy_folder(lib_path, os.path.join(TMP_DIR, "pillow.libs"))
        if base_file_name == "__init__.py":
            # its really a folder
            move_files_to_tmp_and_clean(
                os.path.dirname(module.__file__),
                TMP_DIR,
                module_name,
                sub_modules_to_skip,
            )
        else:
            # its just one file
            clean_file_and_copy(
                module.__file__,
                os.path.join(TMP_DIR, base_file_name),
                module_name,
                module_name,
            )

    warn_unused_code_skips()

    if args.skip_nuitka:
        sys.exit(0)

    delete_folder(COMPILE_DIR)
    input_file: str = f"{TMP_DIR}/{FILE}.py"
    default_python: str = "python" if os.name == "nt" else "bin/python3"
    python_path: str = f"{sys.exec_prefix}/{default_python}"
    process: Popen = start_nuitka_compilation(
        python_path, input_file, WORKING_DIR, nuitka_args
    )

    print("Waiting for nuitka compilation...")

    install_path: str = args.install_path if not args.debug else COMPILE_DIR

    if process.wait():
        sys.exit(1)

    for data_file_path in DATA_FILE_PATHS:
        old_path = os.path.join(CODE_DIR, data_file_path)
        new_path = os.path.join(COMPILE_DIR, data_file_path)
        os.makedirs(os.path.dirname(new_path), exist_ok=True)
        copy_file(old_path, new_path)

    if args.build_info_file:
        with open(
            os.path.join(COMPILE_DIR, BUILD_INFO_FILE), "w", encoding="utf-8"
        ) as fp:
            fp.write(f"OS: {os.name}\n")
            fp.write(f"Python: {sys.version}\n")
            fp.write("Dependencies:\n")
            for module in module_dependencies:
                name: str = module.name
                fp.write(f"\t{name}: {get_module_version(name)}\n")
            fp.write(f"Arguments: {args}\n")

    if is_standalone:
        clean_tk_files(COMPILE_DIR)
        if args.strip:
            strip_files(COMPILE_DIR)
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
        delete_file(os.path.join(WORKING_DIR, f"{FILE}.cmd"))

print("\nFinished")
print("Installed to", install_path)

install_byte_size: int = get_folder_size(install_path)
print(f"Install Size: {install_byte_size:,} bytes")
