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

1. (Linux) Install *libjpeg-turbo-official*.

1. Install *gcc* to compile \*.c into python module extensions and *make* to run Makefile commands.

1. Run 'make build-all' to build all \*.pyd/\*.so python module extensions.

1. Run 'pip install -r requirements.txt' to install python dependencies.

1. Run 'python \_\_main\_\_.py "C:/example/path/to/image.png"' to start the program.

## Instructions To Compile

1. Complete steps in [Instructions To Get It Running](#instructions-to-get-it-running)

1. Run 'pip install -r requirements_compile.txt' to install python dependencies for compilation.

1. Run 'make install' (recommended) or 'python compile.py' as root. On Linux use sudo or on Windows run your terminal as admin. This will compile the code and install it into a default directory. You can edit the install path, and many other things, with various flags you can pass to compile.py. Run 'python compile.py -h' to list them.

# Development

I am currently the only dev and tend to work on Windows. I have a Linux laptop that I periodically check things on, but due to this being a UI app, I can't cover everything with a unit test. Its possible I break Linux compatibility from time to time, so be warned.

# Other Info

For simplicity I include the turbo jpeg dll in this repo, according to turbo jpeg's license I must state:
This software is based in part on the work of the Independent JPEG Group.
