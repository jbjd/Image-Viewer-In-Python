import ctypes
import os
import shutil
import subprocess

try:
    import nuitka  # noqa: F401
except ImportError:
    raise ImportError(
        "Nuitka is not installed on your system, it must be installed to compile"
    )


# only works for windows currently
if os.name == "nt":
    is_admin: bool = ctypes.windll.shell32.IsUserAnAdmin() != 0
else:
    raise Exception("Compiling on Linux/Mac not currently supported")

if not is_admin:
    raise Exception("compile.py needs admin privileges to run")

WORKING_DIR: str = f"{os.path.dirname(os.path.realpath(__file__))}/"
INSTALL_PATH: str = "C:/Program Files/Personal Image Viewer/"
TEMP_PATH: str = f"{WORKING_DIR}/TEMP/"  # set up here, then copy to install path
DATA_FILE_PATHS: list[str] = ["icon/icon.ico", "dll/libturbojpeg.dll"]


print("Starting up nuitka")
cmd_str = f'python -m nuitka --windows-disable-console \
    --windows-icon-from-ico="{WORKING_DIR}icon/icon.ico" \
    --follow-import-to="factories" --follow-import-to="util" \
    --follow-import-to="image" --follow-import-to="viewer" \
    --follow-import-to="managers"  --follow-import-to="helpers" {WORKING_DIR}main.py'
process = subprocess.Popen(cmd_str, shell=True, cwd=WORKING_DIR)


def cleanup_after_compile() -> None:
    shutil.rmtree(f"{WORKING_DIR}main.build/", ignore_errors=True)
    try:
        os.remove(f"{WORKING_DIR}main.cmd")
    except FileNotFoundError:
        pass


try:
    os.makedirs(INSTALL_PATH, exist_ok=True)

    for data_file_path in DATA_FILE_PATHS:
        old_path: str = f"{WORKING_DIR}{data_file_path}"
        new_path: str = f"{TEMP_PATH}{data_file_path}"
        os.makedirs(os.path.dirname(new_path), exist_ok=True)
        shutil.copy(old_path, new_path)
except Exception as e:
    # stop the compile thread
    process.kill()
    cleanup_after_compile()
    raise e

print("Waiting for nuitka compilation")
process.wait()

os.rename(f"{WORKING_DIR}main.exe", f"{TEMP_PATH}viewer.exe")

# copy temp path to install path
shutil.rmtree(INSTALL_PATH, ignore_errors=True)
os.rename(TEMP_PATH, INSTALL_PATH)

cleanup_after_compile()
print(f"\nFinished, installed to {INSTALL_PATH}")
