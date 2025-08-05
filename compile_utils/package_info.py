"""Information on the image viewer package"""

import os


IMAGE_VIEWER_NAME: str = "image_viewer"

# All modules that nuitka will need to follow imports to
MODULES: list[str] = [
    "actions",
    "animation",
    "config",
    "constants",
    "files",
    "image",
    "state",
    "ui",
    "util",
    "viewer",
]

# Some modules can't be followed normally or need to
# be checked explicitly
STANDALONE_MODULES_TO_INCLUDE: list[str] = [
    "numpy._core._exceptions",
    "util._generic",
]

if os.name == "nt":
    STANDALONE_MODULES_TO_INCLUDE += ["util._os_nt"]
