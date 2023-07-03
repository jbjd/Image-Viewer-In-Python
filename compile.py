import subprocess
import os
from shutil import rmtree

# only works for windows currently
if os.name != 'nt':
	raise Exception("Compiling on Linux/Mac not currently supported")

WORKING_DIR = __file__.replace('\\', '/')
WORKING_DIR = WORKING_DIR[:WORKING_DIR.rfind('/')+1]

if not WORKING_DIR:
	raise Exception("Failed to find this file's directory")

with open(f"{WORKING_DIR}viewer.py", "r") as f:
	lines = f.readlines()
# skip comments and lines used for debug purposes 
with open(f"{WORKING_DIR}temp.py", "w") as f:
	for line in lines:
		if 'DEBUG' not in line and line.lstrip() != '' and line.lstrip()[0] != '#':
			f.write(line)

print('Starting up nuitka')
cmd_str = f'python -m nuitka --windows-disable-console --windows-icon-from-ico="{WORKING_DIR}icon/icon.ico" --mingw64 {WORKING_DIR}temp.py'
process = subprocess.Popen(cmd_str, shell=True, cwd=WORKING_DIR)

try:
	if not os.path.exists("C:/Program Files/Personal Image Viewer/icon/"):
		os.makedirs("C:/Program Files/Personal Image Viewer/icon/")

	if(os.path.isfile('C:/Program Files/Personal Image Viewer/viewer2.exe')):
		os.remove('C:/Program Files/Personal Image Viewer/viewer2.exe')

	if(os.path.isfile('C:/Program Files/Personal Image Viewer/viewer.exe')):
		os.rename('C:/Program Files/Personal Image Viewer/viewer.exe', 'C:/Program Files/Personal Image Viewer/viewer2.exe')

	if not os.path.exists("C:/Program Files/Personal Image Viewer/icon/"):
		os.makedirs("C:/Program Files/Personal Image Viewer/icon/")

	os.system(f'copy "{os.path.abspath(WORKING_DIR+"icon/icon.ico")}" "{os.path.abspath("C:/Program Files/Personal Image Viewer/icon/icon.ico")}"')

	if not os.path.exists("C:/Program Files/Personal Image Viewer/util/Win/"):
		print('Made dir for dll')
		os.makedirs("C:/Program Files/Personal Image Viewer/util/Win/")
	elif os.path.exists("C:/Program Files/Personal Image Viewer/util/Win/util.dll"):
		print('Deleting old dll')
		os.remove("C:/Program Files/Personal Image Viewer/util/Win/util.dll")
	os.system(f'copy "{os.path.abspath(WORKING_DIR+"util/Win/util.dll")}" "{os.path.abspath("C:/Program Files/Personal Image Viewer/util/Win/util.dll")}"')
	print('dll updated')

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