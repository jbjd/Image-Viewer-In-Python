import subprocess
import os

cmd_str = 'python -m nuitka --windows-disable-console --windows-icon-from-ico="C:\PythonCode\Viewer\icon\icon.ico" --mingw64 viewer.py'
process = subprocess.Popen(cmd_str, shell=True)


if(os.path.isfile('C:/Program Files/Personal Image Viewer/viewer2.exe')):
	os.remove('C:/Program Files/Personal Image Viewer/viewer2.exe')

if(os.path.isfile('C:/Program Files/Personal Image Viewer/viewer.exe')):
	os.rename('C:/Program Files/Personal Image Viewer/viewer.exe', 'C:/Program Files/Personal Image Viewer/viewer2.exe')

process.wait()
os.rename('C:/PythonCode/Viewer/viewer.exe', 'C:/Program Files/Personal Image Viewer/viewer.exe')