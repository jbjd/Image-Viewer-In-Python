"""Functions to help with calling nuitka"""

import os
from subprocess import Popen

from compile_utils.package_info import MODULES


def get_base_cmd_args(python_path: str, input_file: str) -> list[str]:
    """Returns the base cmd commands that this package uses to compile"""
    cmd_args: list[str] = [
        python_path,
        "-m",
        "nuitka",
        input_file,
        "--python-flag=-OO,no_annotations,no_warnings",
        "--output-filename=viewer",
    ]

    for module in MODULES:
        cmd_args.append(f"--follow-import-to={module}")

    return cmd_args


def start_nuitka_compilation(
    python_path: str, input_file: str, working_dir: str, extra_nuitka_args: list[str]
) -> Popen:
    """Begins nuitka compilation in another process"""

    print("Starting compilation with nuitka")
    print(f'Using python install "{python_path}"')

    compile_env = os.environ.copy()
    compile_env["CCFLAGS"] = "-O2"

    args: list[str] = get_base_cmd_args(python_path, input_file)
    args += extra_nuitka_args

    return Popen(args, cwd=working_dir, env=compile_env)
