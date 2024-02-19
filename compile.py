import os
import shutil
import subprocess
from argparse import REMAINDER, ArgumentParser
from glob import glob
from importlib import import_module
from sys import version_info

from compile_utils.cleaner import clean_file_and_copy

try:
    from nuitka import PythonVersions
except ImportError:
    raise ImportError(
        "Nuitka is not installed on your system, it must be installed to compile"
    )

if version_info[:2] < (3, 10):
    raise Exception("Python 3.10 or higher required")

if (
    version := f"{version_info[0]}.{version_info[1]}"
) in PythonVersions.getNotYetSupportedPythonVersions():
    raise Exception(f"{version} not supported by Nuitka yet")

WORKING_DIR: str = os.path.abspath(os.path.dirname(__file__))
TMP_DIR: str = os.path.join(WORKING_DIR, "tmp")
CODE_DIR: str = os.path.join(WORKING_DIR, "image_viewer")
COMPILE_DIR: str = os.path.join(WORKING_DIR, "main.dist")
VALID_NUITKA_ARGS: set[str] = {
    "--mingw64",
    "--clang",
    "--standalone",
    "--enable-console",
}
install_path: str
executable_ext: str
data_file_paths: list[str]

is_windows: bool = os.name == "nt"
if is_windows:
    install_path = "C:/Program Files/Personal Image Viewer/"
    executable_ext = ".exe"
    data_file_paths = ["icon/icon.ico", "dll/libturbojpeg.dll"]
else:
    install_path = "/usr/local/personal-image-viewer/"
    executable_ext = ".bin"
    data_file_paths = ["icon/icon.png"]

parser = ArgumentParser(
    description="Compiles Personal Image Viewer to an executable, must be run as root",
    epilog=f"Some nuitka arguments are also accepted: {VALID_NUITKA_ARGS}\n",
)
parser.add_argument("-p", "--python-path", help="Python path to use in compilation")
parser.add_argument(
    "--install-path", help=f"Path to install to, default is {install_path}"
)
parser.add_argument(
    "--report",
    action="store_true",
    help="Adds --report=compilation-report.xml flag to nuitka",
)
parser.add_argument(
    "--debug",
    action="store_true",
    help=(
        "Doesn't move compiled code to install path, doesn't check for root, "
        "doesn't pass Go, doesn't collect $200, "
        "adds --enable-console, --warn-implicit-exceptions, --warn-unusual-code,"
        " --report=compilation-report.xml flags to nuitka"
    ),
)
parser.add_argument("args", nargs=REMAINDER)
args, extra_args_list = parser.parse_known_args()
for extra_arg in extra_args_list:
    if extra_arg not in VALID_NUITKA_ARGS:
        raise ValueError(f"Unkown arguement {extra_arg}")

extra_args: str = " ".join(extra_args_list).strip()
as_standalone: bool = "--standalone" in extra_args_list

if args.report or args.debug:
    extra_args += " --report=compilation-report.xml"
    if args.debug:
        extra_args += " --warn-implicit-exceptions --warn-unusual-code"

if as_standalone:
    extra_args += " --enable-plugin=tk-inter"
    with open(os.path.join(WORKING_DIR, "skippable_imports.txt")) as fp:
        extra_args += " --nofollow-import-to=" + " --nofollow-import-to=".join(
            fp.read().strip().split("\n")
        )

extra_args += (
    " --enable-console"
    if "--enable-console" in extra_args_list or args.debug
    else " --disable-console"
)

if not args.debug:
    is_root: bool
    if is_windows:
        import ctypes

        is_root = ctypes.windll.shell32.IsUserAnAdmin() != 0
    else:
        # On windows, mypy complains
        is_root = os.geteuid() == 0  # type: ignore

    if not is_root:
        raise Exception("compile.py needs root privileges to run")

if args.python_path is None:
    if is_windows:
        # if not provided, try to find with where
        args.python_path = (
            subprocess.run("where python", shell=True, stdout=subprocess.PIPE)
            .stdout.decode()
            .partition("\n")[0]
        )
        if args.python_path == "":
            raise Exception(
                (
                    "Failed to find path to python. "
                    "Please provide the --python-path command line argument"
                )
            )
    else:
        args.python_path = "python3"


def move_files_to_tmp_and_clean(dir: str, mod_prefix: str = ""):
    for python_file in glob(f"{dir}/**/*.py", recursive=True):
        if os.path.basename(python_file) == "__main__.py" and mod_prefix != "":
            continue
        python_file = os.path.abspath(python_file)
        relative_path: str = os.path.join(
            mod_prefix, python_file.replace(dir, "").strip("/\\")
        )
        new_path: str = os.path.join(TMP_DIR, relative_path)
        clean_file_and_copy(python_file, new_path)


# Before compiling, copy to tmp dir and remove type-hints/clean code
# I thought nuitka would handle this, but I guess not?
shutil.rmtree(TMP_DIR, ignore_errors=True)
try:
    move_files_to_tmp_and_clean(CODE_DIR)

    for mod_name in ["turbojpeg", "send2trash"]:  # TODO: add more
        module = import_module(mod_name)
        if module.__file__ is None:
            print(f"Error getting module {mod_name}'s filepath")
            continue
        base_file_name: str = os.path.basename(module.__file__)
        if base_file_name == "__init__.py":
            # its really a folder
            move_files_to_tmp_and_clean(os.path.dirname(module.__file__), mod_name)
        else:
            # its just one file
            clean_file_and_copy(
                module.__file__,
                os.path.join(TMP_DIR, base_file_name),
                mod_name,
            )

    # Begin nuitka compilation in subprocess
    print("Starting compilation with nuitka")
    print("Using python install ", args.python_path)
    cmd_str = f'{args.python_path} -m nuitka --follow-import-to="factories" \
        --follow-import-to="helpers" --follow-import-to="util" --follow-import-to="ui" \
        --follow-import-to="viewer" --follow-import-to="managers" {extra_args} \
        --windows-icon-from-ico="{CODE_DIR}/icon/icon.ico" \
        --python-flag="-OO,no_annotations,no_warnings" "{TMP_DIR}/main.py"'

    process = subprocess.Popen(cmd_str, shell=True, cwd=WORKING_DIR)

    if args.install_path:
        install_path = args.install_path

    os.makedirs(install_path, exist_ok=True)

    print("Waiting for nuitka compilation...")
    process.wait()

    for data_file_path in data_file_paths:
        old_path = os.path.join(CODE_DIR, data_file_path)
        new_path = os.path.join(COMPILE_DIR, data_file_path)
        os.makedirs(os.path.dirname(new_path), exist_ok=True)
        shutil.copy(old_path, new_path)

    if args.debug:
        exit(0)

    dest: str = os.path.join(COMPILE_DIR, f"viewer{executable_ext}")
    src: str = os.path.join(
        COMPILE_DIR if as_standalone else WORKING_DIR, f"main{executable_ext}"
    )
    os.rename(src, dest)
    shutil.rmtree(install_path, ignore_errors=True)
    os.rename(COMPILE_DIR, install_path)
finally:
    if not args.debug:
        shutil.rmtree(os.path.join(WORKING_DIR, "main.build"), ignore_errors=True)
        shutil.rmtree(COMPILE_DIR, ignore_errors=True)
        shutil.rmtree(TMP_DIR, ignore_errors=True)
        try:
            os.remove(os.path.join(WORKING_DIR, "main.cmd"))
        except FileNotFoundError:
            pass

print("\nFinished")
print("Installed to", install_path)
