"""Functions to help with calling nuitka"""

import os
from subprocess import Popen

from compile_utils.args import NuitkaArgs
from compile_utils.code_to_skip import data_files_to_exclude, dlls_to_exclude
from compile_utils.module_dependencies import modules_to_include


def start_nuitka_compilation(
    python_path: str,
    input_file: str,
    code_dir: str,
    working_dir: str,
    nuitka_args: list[str],
    files_to_include: list[str],
) -> Popen:
    """Begins nuitka compilation in another process"""

    print("Starting compilation with nuitka")
    print(f'Using python install "{python_path}"')

    compile_env = os.environ.copy()
    # -march=native had a race condition that segfaulted on startup
    # -mtune=native works as intended
    compile_env["CFLAGS"] = "-O3 -fno-signed-zeros -mtune=native"

    command: list[str] = get_nuitka_command(
        code_dir, python_path, input_file, nuitka_args, files_to_include
    )

    return Popen(command, cwd=working_dir, env=compile_env)


def get_nuitka_command(
    code_dir: str,
    python_path: str,
    input_file: str,
    nuitka_args: list[str],
    files_to_include: list[str],
) -> list[str]:
    """Returns the command that this package uses to compile"""
    command: list[str] = (
        [
            python_path,
            "-OO",
            "-m",
            "nuitka",
            input_file,
            "--python-flag=-OO,no_annotations,no_warnings,static_hashes",
            "--output-filename=viewer",
        ]
        + nuitka_args
        + [
            f"--include-data-files={os.path.join(code_dir, file)}={file}"
            for file in files_to_include
        ]
        + [f"--include-module={module}" for module in modules_to_include]
        + [f"--noinclude-data-files={glob}" for glob in data_files_to_exclude]
        + [f"--noinclude-dlls={glob}" for glob in dlls_to_exclude]
    )

    return command


def has_standalone_flag(nuitka_args: list[str]) -> bool:
    return NuitkaArgs.STANDALONE in nuitka_args
