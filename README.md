# Personal Image Viewer

A lightweight "Personal Image Viewer" written in Python 3.12

## Supported File Types

PNG, JPEG, WebP, AVIF, GIF, DDS

Animation support for PNG/WebP/GIF

## Description

An image viewer with the intent of being clean and simple; Images are fit to your screen in the best quality without
the clutter that other image viewers have.

Features Include:
* Optimized JPEG decoding with turbojpeg
* Renaming/Conversion/Deletion of images
* Undoing rename/convert/delete
* Drop via clipboard (Windows only)
* Exporting image as base64

Feel free to take this code and edit it however you like. Please don't use it for commercial purposes.

# Instructions To Get It Running

1. Have Python 3.12.x installed.

2. Linux Users: you will need to install libjpeg-turbo-official

3. Install pip packages listed in requirements.txt, this can be done with "pip install -r requirements.txt".

4. Use 'python \_\_main\_\_.py "C:/example/path/to/image.png"' to run it, or continue to convert it to an executable.

5. Install requirements to compile with "pip install -r requirements_compile.txt".

6. Run 'make install' (recommended) or 'python compile.py' as root. On Linux use sudo or on Windows run your terminal as admin. This will compile the code and install it into a default directory. You can edit the install path, and many other things, with various flags you can pass to compile.py. Run 'python compile.py -h' to list them.

7. To use it as an exe on Windows, go to an image file and right-click > select 'open with' > 'Choose another app' > select the exe file you just created.

# Development

I am currently the only dev and tend to work on Windows. I have a Linux laptop that I periodically check things on, but due to this being a UI app, I can't cover everything with a unit test. Its possible I break Linux compatibility from time to time, so be warned.

# Other Info

For simplicity I include the turbo jpeg dll in this repo, according to turbo jpeg's license I must state:
This software is based in part on the work of the Independent JPEG Group.
