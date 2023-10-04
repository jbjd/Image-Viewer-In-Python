# Image-Viewer-In-Python
a Lightweight Image Viewer written in Python 3.11

An image viewer with the intent of being fast and simple; Images are fit to your screen in the best quality. Currently includes a button for deletion, renaming a file,
and file info, but more features might be added in the future. All buttons are on a transparent bar that comes and goes when you click, so nothing clutters the screen. Supports png, jpegs, webp, gifs, and bitmaps. Animated files are supported for png, webp, and gifs.

Other features/plans:
- More data on file info tab
- Searching
- Cropping

Feel free to take this code and edit it however you like.

# Instructions to get it running:

1. Have Python 3.9+ installed (along with nuitka if you want to convert it to an .exe file).
2. Install Pip packages listed in requirements.txt, this can be done with "pip install -r requirements.txt"
  
3. Use 'python viewer.py "C:/example/path/to/image.png"' to run it, or continue following to convert it to an exe if using Windows. I currently don't support Linux/Mac but might in the future. 

4. Install Nuitka with the command 'python -m pip install -U nuitka' This is a compiler which converts Python to an exe. pyinstaller is also an option but it loads much slower and the file is larger, thus I strongly reccomend nuitka.

5. Run "python compile.py" or the full path to compile.py if not currently in the same directory. This will install it into your program files directory -> C:/Program Files/Personal Image Viewer/viewer.exe

6. To use it as an exe, go to an image file and right-click > select 'open with' > 'Choose another app' > select the exe file

For simplicity I include the turbo jpeg dll in this repo, according to turbo jpeg's liscense I must state:
This software is based in part on the work of the Independent JPEG Group.
