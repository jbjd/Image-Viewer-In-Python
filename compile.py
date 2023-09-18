import subprocess
import os
from shutil import rmtree
import re

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
if os.name != 'nt':
	raise Exception("Compiling on Linux/Mac not currently supported")

WORKING_DIR = __file__.replace('\\', '/')
WORKING_DIR = WORKING_DIR[:WORKING_DIR.rfind('/')+1]

if not WORKING_DIR:
	raise Exception("Failed to find this file's directory")

with open(f"{WORKING_DIR}viewer.py", "r") as f:
	lines = f.readlines()
lines_without_debug = []
# skip comments and lines used for debug purposes
for line in lines:
	if 'DEBUG' not in line and line.lstrip() != '' and line.lstrip()[0] != '#':
		lines_without_debug.append(line.replace('    ', '	'))  # also replaces all 4 spaces with tabs for consistency
lines.clear()
# make new temp py file to compile with that discards lines of code that only run on other operating systems
if os.name == 'nt':
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
				if lines_without_debug[i].lstrip()[:4] == 'else':
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

print('Starting up nuitka')
cmd_str = f'python -m nuitka --windows-disable-console --windows-icon-from-ico="{WORKING_DIR}icon/icon.ico" --mingw64 {WORKING_DIR}temp.py'
process = subprocess.Popen(cmd_str, shell=True, cwd=WORKING_DIR)

try:
	if not os.path.exists("C:/Program Files/Personal Image Viewer/icon/"):
		os.makedirs("C:/Program Files/Personal Image Viewer/icon/")

	if os.path.isfile('C:/Program Files/Personal Image Viewer/viewer2.exe'):
		os.remove('C:/Program Files/Personal Image Viewer/viewer2.exe')

	if os.path.isfile('C:/Program Files/Personal Image Viewer/viewer.exe'):
		os.rename('C:/Program Files/Personal Image Viewer/viewer.exe', 'C:/Program Files/Personal Image Viewer/viewer2.exe')

	if not os.path.exists("C:/Program Files/Personal Image Viewer/icon/"):
		os.makedirs("C:/Program Files/Personal Image Viewer/icon/")

	os.system(f'copy "{os.path.abspath(WORKING_DIR+"icon/icon.ico")}" "{os.path.abspath("C:/Program Files/Personal Image Viewer/icon/icon.ico")}"')

	print('Waiting for nuitka compilation')
	process.wait()
	os.remove(f'{WORKING_DIR}temp.py')
	rmtree(WORKING_DIR+'temp.build')
	os.remove(WORKING_DIR+'temp.cmd')
	os.rename(WORKING_DIR+'temp.exe', 'C:/Program Files/Personal Image Viewer/viewer.exe')

except Exception as e:
	print(e)
	print("No root privileges, please run as admin")
	process.kill()
	exit(0)
