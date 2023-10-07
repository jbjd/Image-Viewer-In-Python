import subprocess
import os
from shutil import rmtree
import re
from distutils.dir_util import copy_tree

try:
	import nuitka  # noqa: F401
except ImportError:
	raise ImportError("Nuitka is not installed on your system, it must be installed to compile")


# returns tabs on left side of string
def countTabLevel(line: str):
	tabs = 0
	for char in line.rstrip():
		if char == '\t':
			tabs += 1
		else:
			break
	return tabs


# only works for windows currently
if os.name != "nt":
	raise Exception("Compiling on Linux/Mac not currently supported")

INSTALL_PATH = "C:/Program Files/Personal Image Viewer/"

WORKING_DIR = __file__.replace('\\', '/')
WORKING_DIR = WORKING_DIR[:WORKING_DIR.rfind('/')+1]

if not WORKING_DIR:
	raise Exception("Failed to find this file's directory")

with open(f"{WORKING_DIR}viewer.py", "r") as f:
	lines = f.readlines()
lines_without_debug = []
# skip comments and lines used for debug purposes
for line in lines:
	if "DEBUG" not in line and line.lstrip() != "" and line.lstrip()[0] != '#':
		lines_without_debug.append(line.replace("    ", "	"))  # also replaces all 4 spaces with tabs for consistency
lines.clear()
# make new temp py file to compile with that discards lines of code that only run on other operating systems
if os.name == "nt":
	with open(f"{WORKING_DIR}temp.py", "w") as f:
		i = 0
		while i < len(lines_without_debug):
			line = lines_without_debug[i]
			if re.search("if[ 	(]+os.name[ 	]*==[ 	]*('nt'|\"nt\")", line):
				tabLevel = countTabLevel(line)
				i += 1
				while i < len(lines_without_debug) and countTabLevel(lines_without_debug[i]) > tabLevel:
					f.write(lines_without_debug[i][1:])
					i += 1
				if lines_without_debug[i].lstrip()[:4] == "else":
					tabLevel = countTabLevel(lines_without_debug[i])
					i += 1
					while i < len(lines_without_debug) and countTabLevel(lines_without_debug[i]) > tabLevel:
						i += 1
			else:
				f.write(line)
				i += 1
else:
	with open(f"{WORKING_DIR}temp.py", "w") as f:
		for line in lines_without_debug:
			f.write(line)

print("Starting up nuitka")
cmd_str = f'python -m nuitka --windows-disable-console --windows-icon-from-ico="{WORKING_DIR}icon/icon.ico" --mingw64 --follow-import-to="factories" {WORKING_DIR}temp.py'
process = subprocess.Popen(cmd_str, shell=True, cwd=WORKING_DIR)

try:
	# keeps a copy of previously installed version just in case
	exe_install_path = f"{INSTALL_PATH}viewer.exe"
	old_exe_install_path = f"{INSTALL_PATH}viewer2.exe"

	if os.path.isfile(old_exe_install_path):
		os.remove(old_exe_install_path)

	if os.path.isfile(exe_install_path):
		os.rename(exe_install_path, old_exe_install_path)

	# data files
	copy_tree(f"{WORKING_DIR}icon/", f"{INSTALL_PATH}icon")
	copy_tree(f"{WORKING_DIR}util/", f"{INSTALL_PATH}util")

	print("Waiting for nuitka compilation")
	process.wait()
	os.remove(f"{WORKING_DIR}temp.py")
	os.remove(f"{WORKING_DIR}temp.cmd")
	os.rename(f"{WORKING_DIR}temp.exe", exe_install_path)
	rmtree(f"{WORKING_DIR}temp.build")

except Exception as e:
	print(e)
	print("This is probably due to a lack of root privileges, please run as root")
	process.kill()
	exit(0)
