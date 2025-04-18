import ctypes

dll = ctypes.PyDLL("C:/Python/Viewer/image_viewer/c_extensions/os.dll")
create_list = dll.create_list
create_list.argtypes = [ctypes.py_object]
create_list.restype = ctypes.py_object

a = create_list("C:/photos/*")
print(a)
