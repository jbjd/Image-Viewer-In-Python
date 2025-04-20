PYTHON_PATH := $(shell python -c "import sys;print(sys.exec_prefix)")

build_dll:
	gcc image_viewer/c_extensions/util.c -L$(PYTHON_PATH)/libs/ -I$(PYTHON_PATH)/include/ -lpython312 -O3 -s -shared -o image_viewer/dll/util.dll


