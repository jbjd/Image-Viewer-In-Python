"""A script to compile the image viewer into an executable file via nuitka"""

import os
import sys
from importlib import import_module
from importlib.metadata import version as get_module_version
from subprocess import Popen

from personal_compile_tools.file_operations import (
    copy_file,
    copy_folder,
    delete_file,
    delete_folder,
    delete_folders,
    get_folder_size,
)

from compile_utils.args import CompileArgumentParser, CompileNamespace, NuitkaArgs
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
    raise_if_not_root,
    validate_module_requirements,
    validate_python_version,
)

validate_python_version()

WORKING_FOLDER: str = os.path.normpath(os.path.dirname(__file__))
FILE: str = "__main__"
TMP_FOLDER: str = os.path.join(WORKING_FOLDER, "tmp")
CODE_FOLDER: str = os.path.join(WORKING_FOLDER, IMAGE_VIEWER_NAME)
COMPILE_FOLDER: str = os.path.join(WORKING_FOLDER, f"{FILE}.dist")
BUILD_FOLDER: str = os.path.join(WORKING_FOLDER, f"{FILE}.build")

EXECUTABLE_EXT: str
DEFAULT_INSTALL_PATH: str
files_to_include: list[str] = ["config.ini"]

if os.name == "nt":
    EXECUTABLE_EXT = ".exe"
    DEFAULT_INSTALL_PATH = "C:/Program Files/Personal Image Viewer/"
    files_to_include += ["icon/icon.ico"]
else:
    EXECUTABLE_EXT = ".bin"
    DEFAULT_INSTALL_PATH = "/usr/local/personal-image-viewer/"
    files_to_include += ["icon/icon.png"]

EXECUTABLE_NAME: str = "viewer" + EXECUTABLE_EXT

parser = CompileArgumentParser(DEFAULT_INSTALL_PATH)

args: CompileNamespace
nuitka_args: list[str]
args, nuitka_args = parser.parse_known_args(modules_to_skip)

if not args.debug and not args.skip_nuitka:
    raise_if_not_root()

if os.name == "nt":
    nuitka_args += [
        NuitkaArgs.MINGW64,
        NuitkaArgs.WINDOWS_ICON_FROM_ICO.with_value(f"{CODE_FOLDER}/icon/icon.ico"),
    ]

validate_module_requirements()

delete_folder(TMP_FOLDER)
try:
    move_files_to_tmp_and_clean(CODE_FOLDER, TMP_FOLDER, IMAGE_VIEWER_NAME)

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
        if module_name == "PIL" and os.name != "nt":
            site_packages_path = os.path.dirname(os.path.dirname(module.__file__))
            lib_path = os.path.join(site_packages_path, "pillow.libs")
            copy_folder(lib_path, os.path.join(TMP_FOLDER, "pillow.libs"))
        if base_file_name == "__init__.py":
            # its really a folder
            move_files_to_tmp_and_clean(
                os.path.dirname(module.__file__),
                TMP_FOLDER,
                module_name,
                sub_modules_to_skip,
            )
        else:
            # its just one file
            clean_file_and_copy(
                module.__file__,
                os.path.join(TMP_FOLDER, base_file_name),
                module_name,
                module_name,
            )

    warn_unused_code_skips()

    if args.skip_nuitka:
        sys.exit(0)

    delete_folder(COMPILE_FOLDER)
    input_file: str = f"{TMP_FOLDER}/{FILE}.py"
    default_python: str = "python" if os.name == "nt" else "bin/python3"
    python_path: str = f"{sys.exec_prefix}/{default_python}"
    process: Popen = start_nuitka_compilation(
        python_path, input_file, WORKING_FOLDER, nuitka_args
    )

    print("Waiting for nuitka compilation...")

    install_path: str = args.install_path if not args.debug else COMPILE_FOLDER

    if process.wait():
        sys.exit(1)

    for data_file_path in files_to_include:
        old_path = os.path.join(CODE_FOLDER, data_file_path)
        new_path = os.path.join(COMPILE_FOLDER, data_file_path)
        os.makedirs(os.path.dirname(new_path), exist_ok=True)
        copy_file(old_path, new_path)

    if args.build_info_file:
        with open(
            os.path.join(COMPILE_FOLDER, BUILD_INFO_FILE), "w", encoding="utf-8"
        ) as fp:
            fp.write(f"OS: {os.name}\n")
            fp.write(f"Python: {sys.version}\n")
            fp.write("Dependencies:\n")
            for module in module_dependencies:
                name: str = module.name
                fp.write(f"\t{name}: {get_module_version(name)}\n")
            fp.write(f"Arguments: {args}\n")

    clean_tk_files(COMPILE_FOLDER)
    if args.strip:
        strip_files(COMPILE_FOLDER)

    if not args.debug:
        delete_folder(install_path)
        os.rename(COMPILE_FOLDER, install_path)
finally:
    if not args.debug and not args.no_cleanup:
        delete_folders([BUILD_FOLDER, COMPILE_FOLDER, TMP_FOLDER])
        delete_file(os.path.join(WORKING_FOLDER, f"{FILE}.cmd"))

print("\nFinished")
print("Installed to", install_path)

install_byte_size: int = get_folder_size(install_path)
print(f"Install Size: {install_byte_size:,} bytes")
