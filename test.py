import ctypes
from time import perf_counter

dll = ctypes.PyDLL("C:/Python/Viewer/image_viewer/c_extensions/os.dll")
create_list = dll.create_list
create_list.argtypes = [ctypes.py_object]
create_list.restype = ctypes.py_object

a = perf_counter()
list_of_image_paths = create_list("A:/hh/Imaj/*")
print(perf_counter() - a)
# print(list_of_image_paths)
