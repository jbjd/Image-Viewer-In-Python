PYTHON_PATH := $(shell python -c "import sys;print(sys.exec_prefix)")

build_dll_windows:
	gcc image_viewer/c_extensions/os_util_nt.c -L$(PYTHON_PATH)/libs/ -I$(PYTHON_PATH)/include/ -lpython312 -O3 -s -shared -o image_viewer/dll/os_util_nt.dll -Wall -Werror


