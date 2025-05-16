"""Information on the image viewer package"""

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
