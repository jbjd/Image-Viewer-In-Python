import subprocess
import os
from shutil import rmtree

WORKING_DIR = 'C:/PythonCode/Viewer/'

cmd_str = f'python -m nuitka --windows-disable-console --windows-icon-from-ico="{WORKING_DIR}icon/icon.ico" --mingw64 {WORKING_DIR}viewer.py'
process = subprocess.Popen(cmd_str, shell=True, cwd=WORKING_DIR)

try:
	if(os.path.isfile('C:/Program Files/Personal Image Viewer/viewer2.exe')):
		os.remove('C:/Program Files/Personal Image Viewer/viewer2.exe')

	if(os.path.isfile('C:/Program Files/Personal Image Viewer/viewer.exe')):
		os.rename('C:/Program Files/Personal Image Viewer/viewer.exe', 'C:/Program Files/Personal Image Viewer/viewer2.exe')

	process.wait()
	rmtree(WORKING_DIR+'viewer.build')
	os.remove(WORKING_DIR+'viewer.cmd')
	os.rename(WORKING_DIR+'viewer.exe', 'C:/Program Files/Personal Image Viewer/viewer.exe')
except Exception as e:
	print(e)
	print("No root privileges")