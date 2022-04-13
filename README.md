# Image-Viewer-In-Python
a Lightweight Image Viewer written in Python 3.9

An image viewer with the intent of being fast and simple; Images are always fullscreened and in high quality. Currently includes a button for deletion, renaming,
and file info, but more features might be added in the future. All buttons are on a transparent bar that comes and goes when you click, so nothing clutters the screen.

Other features I plan to add:
- ~~GIF support~~
- Searching
- More data on file info tab
- Make GIF loading faster

Feel free to take this code and edit it however you like.

# Instructions to get it running:

1. Have python 3.9+ installed (along with nuitka if you want to convert it to an .exe file).
2. Make sure your python has all the following Packages which you can use 'pip' to install:
  - sys
  - tkinter
  - PIL
  - os
  - send2trash
  - pathlib
  - ctypes
  - cython
  - bisect
  - IO
  - natsort

  Credit to bongdang for making the gifraw class that fixes gifs with unqiue frame palettes. I use an edited version of this class, but I mainly just removed parts 
  that I didn't use.
  
3. Use 'python viewer.py "C:/example/path/to/image.png"' to run it, or continue following to convert it to an exe

4. Install Nuitka with the command 'python -m pip install -U nuitka' This is a compiler which converts Python to C. pyinstaller is also an option but it loads slower and the file is much larger, thus I reccomend nuitka.

5. Convert the python file to an exe with the command 'python -m nuitka --windows-disable-console viewer.py'. Without the "--windows-disable-console" flag, it will open a console in the background that does nothing. You should also include --include-plugin-directory=C:\Example\Path\to\gifraw if you want GIF support

6. To use it as an exe, go to an image file and right-click > select 'open with' > 'Choose another app' > select the exe file
