"""Functions to help with calling nuitka"""

import os
from subprocess import Popen


def start_nuitka_compilation(
    python_path: str, input_file: str, working_dir: str, nuitka_args: list[str]
) -> Popen:
    """Begins nuitka compilation in another process"""

    print("Starting compilation with nuitka")
    print("Using python install", python_path)

    compile_env = os.environ.copy()
    # -march=native had a race condition that segfaulted on startup
    # -mtune=native works as intended
    compile_env["CFLAGS"] = "-O3 -fno-signed-zeros -mtune=native"

    command: list[str] = get_nuitka_command(python_path, input_file, nuitka_args)

    return Popen(command, cwd=working_dir, env=compile_env)


def get_nuitka_command(
    python_path: str, input_file: str, nuitka_args: list[str]
) -> list[str]:
    """Returns the command that this package uses to compile"""
    command: list[str] = [
        python_path,
        "-OO",
        "-m",
        "nuitka",
        input_file,
        "--python-flag=-OO,no_annotations,no_warnings,static_hashes",
        "--output-filename=viewer",
    ] + nuitka_args

    return command
