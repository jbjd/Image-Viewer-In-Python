import ctypes
import os
import subprocess
from distutils.dir_util import copy_tree, remove_tree

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

INSTALL_PATH: str = "C:/Program Files/Personal Image Viewer/"

WORKING_DIR: str = f"{os.path.dirname(os.path.realpath(__file__))}/"

if not WORKING_DIR:
    raise Exception("Failed to find this file's directory")


print("Starting up nuitka")
cmd_str = f'python -m nuitka --windows-disable-console \
    --windows-icon-from-ico="{WORKING_DIR}icon/icon.ico" \
    --follow-import-to="factories" --follow-import-to="util" \
    --follow-import-to="image" --follow-import-to="viewer" \
    --follow-import-to="managers"  --follow-import-to="helpers" {WORKING_DIR}main.py'
process = subprocess.Popen(cmd_str, shell=True, cwd=WORKING_DIR)

# keep a copy of previously installed version just in case
exe_install_path = f"{INSTALL_PATH}viewer.exe"
old_exe_install_path = f"{INSTALL_PATH}viewer2.exe"

try:
    if os.path.isfile(old_exe_install_path):
        os.remove(old_exe_install_path)

    if os.path.isfile(exe_install_path):
        os.rename(exe_install_path, old_exe_install_path)

    # data files
    copy_tree(f"{WORKING_DIR}icon/", f"{INSTALL_PATH}icon/")
    copy_tree(f"{WORKING_DIR}dll/", f"{INSTALL_PATH}dll/")

    print("Waiting for nuitka compilation")
    process.wait()
    os.remove(f"{WORKING_DIR}main.cmd")
    os.rename(f"{WORKING_DIR}main.exe", exe_install_path)
    remove_tree(f"{WORKING_DIR}main.build")
    print(f"\nComplete, installed to {INSTALL_PATH}")
finally:
    process.kill()
