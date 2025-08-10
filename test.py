from image_viewer.util._os_nt import get_file_metadata_display
from personal_compile_tools.file_operations import walk_folder
from time import perf_counter
import os
from time import ctime

files = list(walk_folder("A:/hh/Imaj/"))


def get_file_metadata_display_py(path_to_image):
    image_metadata = os.stat(path_to_image)
    created_time_epoch: float = image_metadata.st_birthtime
    modified_time_epoch: float = image_metadata.st_mtime

    # [4:] chops of 3 character day like Mon/Tue/etc.
    created_time: str = ctime(created_time_epoch)[4:]
    modified_time: str = ctime(modified_time_epoch)[4:]
    return f"Created: {created_time}\nLast Modified: {modified_time}\n"


a = perf_counter()

for file in files:
    get_file_metadata_display_py(file)

print(perf_counter() - a)
