import ctypes
import os
import shutil
import subprocess
from argparse import ArgumentParser

try:
    import nuitka  # noqa: F401
except ImportError:
    raise ImportError(
        "Nuitka is not installed on your system, it must be installed to compile"
    )

WORKING_DIR: str = f"{os.path.dirname(os.path.realpath(__file__))}/"
TEMP_PATH: str = f"{WORKING_DIR}TEMP/"  # setup here, then copy to install path
INSTALL_PATH: str
EXECUTABLE_EXT: str
DATA_FILE_PATHS: list[str]

if os.name == "nt":
    INSTALL_PATH = "C:/Program Files/Personal Image Viewer/"
    EXECUTABLE_EXT = ".exe"
    DATA_FILE_PATHS = ["icon/icon.ico", "dll/libturbojpeg.dll"]
else:
    INSTALL_PATH = "/usr/local/personal-image-viewer/"
    EXECUTABLE_EXT = ".bin"
    DATA_FILE_PATHS = ["icon/icon.png"]

parser = ArgumentParser(
    description="Compiles code in this repository to an executable, must be run as root"
)
parser.add_argument("-p", "--python-path", help="Python path to use in compilation")
parser.add_argument(
    "--install-path", help=f"Path to install to, default is {INSTALL_PATH}"
)
args = parser.parse_args()

if args.install_path:
    INSTALL_PATH = args.install_path

is_root: bool
if os.name == "nt":
    is_root = ctypes.windll.shell32.IsUserAnAdmin() != 0
else:
    # On windows, mypy doesn't know this exists
    is_root = os.geteuid() == 0  # type: ignore

if not is_root:
    raise Exception("compile.py needs root privileges to run")

if args.python_path is None:
    if os.name == "nt":
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

# begin nuitka compilation in another thread
print("Starting compilation with nuitka")
print("Using python install found at", args.python_path)
cmd_str = f'{args.python_path} -m nuitka --windows-disable-console \
    --windows-icon-from-ico="{WORKING_DIR}image_viewer/icon/icon.ico" \
    --follow-import-to="factories" --follow-import-to="util" \
    --follow-import-to="viewer" --follow-import-to="managers"  \
    --follow-import-to="helpers" "{WORKING_DIR}image_viewer/main.py"'
process = subprocess.Popen(cmd_str, shell=True, cwd=WORKING_DIR)


def cleanup_after_compile() -> None:
    shutil.rmtree(f"{WORKING_DIR}main.build/", ignore_errors=True)
    try:
        os.remove(f"{WORKING_DIR}main.cmd")
    except FileNotFoundError:
        pass


# setup data files
try:
    os.makedirs(INSTALL_PATH, exist_ok=True)

    for data_file_path in DATA_FILE_PATHS:
        old_path: str = f"{WORKING_DIR}image_viewer/{data_file_path}"
        new_path: str = f"{TEMP_PATH}{data_file_path}"
        os.makedirs(os.path.dirname(new_path), exist_ok=True)
        shutil.copy(old_path, new_path)
except Exception as e:
    # stop the compile thread
    process.kill()
    cleanup_after_compile()
    raise e

print("Waiting for nuitka compilation...")
process.wait()

os.rename(f"{WORKING_DIR}main{EXECUTABLE_EXT}", f"{TEMP_PATH}viewer{EXECUTABLE_EXT}")

# copy temp path to install path
shutil.rmtree(INSTALL_PATH, ignore_errors=True)
os.rename(TEMP_PATH, INSTALL_PATH)

cleanup_after_compile()
print("\nFinished")
print("Installed to", INSTALL_PATH)
