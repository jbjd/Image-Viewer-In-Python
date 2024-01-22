# Personal Image Viewer

A lightweight "Personal Image Viewer" written in Python 3.11

An image viewer with the intent of being clean and simple; Images are fit to your screen in the best quality without
the clutter that other image viewers have. Currently includes a button for deletion, renaming a file,
and file info, but more features might be added in the future. All buttons are on a transparent bar that comes and goes when you click. I Support png, jpeg, webp, gif, and bitmap files including animated versions.

Please see the "todo" file for future plans.
Feel free to take this code and edit it however you like.

# Instructions To Get It Running

1. Have Python 3.10+ installed.

2. Linux Users: you will need to install libjpeg-turbo-official and ttf-mscorefonts-installer

3. Install Pip packages listed in requirements.txt, this can be done with "pip install -r requirements.txt"

4. Use 'python viewer.py "C:/example/path/to/image.png"' to run it, or continue following to convert it to an executable.

5. Install Nuitka with the command 'python -m pip install -U nuitka' This is a compiler which converts Python to an exe. pyinstaller is also an option but it loads much slower and the file is larger, thus I strongly reccomend nuitka.

6. Run "python compile.py" or the full path to compile.py if not currently in the same directory. This will install it into your program files directory -> C:/Program Files/Personal Image Viewer/viewer.exe

7. To use it as an exe, go to an image file and right-click > select 'open with' > 'Choose another app' > select the exe file

# Other Info

For simplicity I include the turbo jpeg dll in this repo, according to turbo jpeg's liscense I must state:
This software is based in part on the work of the Independent JPEG Group.
