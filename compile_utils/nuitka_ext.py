"""Functions to help with calling nuitka"""

import os
from subprocess import Popen

from compile_utils.code_to_skip import data_files_to_exclude, dlls_to_exclude
from compile_utils.module_dependencies import modules_to_include
from compile_utils.package_info import MODULES


def get_base_cmd_args(python_path: str, input_file: str) -> list[str]:
    """Returns the base cmd commands that this package uses to compile"""
    cmd_args: list[str] = (
        [
            python_path,
            "-OO",
            "-m",
            "nuitka",
            input_file,
            "--python-flag=-OO,no_annotations,no_warnings,static_hashes",
            "--output-filename=viewer",
        ]
        + [f"--include-module={module}" for module in modules_to_include]
        + [f"--follow-import-to={module}" for module in MODULES]
        + [f"--noinclude-data-files={glob}" for glob in data_files_to_exclude]
        + [f"--noinclude-dlls={glob}" for glob in dlls_to_exclude]
    )

    return cmd_args


def start_nuitka_compilation(
    python_path: str, input_file: str, working_dir: str, extra_nuitka_args: list[str]
) -> Popen:
    """Begins nuitka compilation in another process"""

    print("Starting compilation with nuitka")
    print(f'Using python install "{python_path}"')

    compile_env = os.environ.copy()
    # -march=native had a race condition that segfaulted on startup
    # -mtune=native works as intended
    compile_env["CFLAGS"] = "-O3 -fno-signed-zeros -mtune=native"

    args: list[str] = get_base_cmd_args(python_path, input_file)
    args += extra_nuitka_args

    return Popen(args, cwd=working_dir, env=compile_env)
