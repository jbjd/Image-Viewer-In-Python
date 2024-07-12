# Personal Image Viewer

A lightweight "Personal Image Viewer" written in Python 3.11

An image viewer with the intent of being clean and simple; Images are fit to your screen in the best quality without
the clutter that other image viewers have. Currently includes a button for deletion, renaming a file,
and file info, but more features might be added in the future. All buttons are on a transparent bar that comes and goes when you click. I support png, jpeg, webp, and gif files including animated versions.

Please see the "todo" file for future plans. However, I don't always update it and will work on unlisted tasks as I feel the need. I made that file just as a place to put my ideas down.

Feel free to take this code and edit it however you like.

# Instructions To Get It Running

1. Have Python 3.11+ installed.

2. Linux Users: you will need to install libjpeg-turbo-official and fonts-roboto

3. Install pip packages listed in requirements.txt, this can be done with "pip install -r requirements.txt".

4. Use 'python3 viewer.py "C:/example/path/to/image.png"' to run it, or continue to convert it to an executable.

5. Install requirements to compile with "pip install -r requirements_compile.txt".

6. Run the compile.py script as root. On Linux use sudo or on windows run your terminal as admin. This will compile the code and install it into a default directory. You can edit the install path, and many other things, with various flags you can pass to compile.py. Run "python3 compile.py -h" to list them.

7. To use it as an exe, go to an image file and right-click > select 'open with' > 'Choose another app' > select the exe file you just created.

# Development

I am currently the only dev and tend to work on windows. I have a linux laptop that I periodically check things on, but due to this being a UI app, I can't cover everything with a unittest. Its possible I break linux compatibility from time to time, so be warned.

# Other Info

For simplicity I include the turbo jpeg dll in this repo, according to turbo jpeg's license I must state:
This software is based in part on the work of the Independent JPEG Group.
