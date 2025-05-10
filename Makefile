ifeq ($(OS),Windows_NT)
    PYTHON := python
else
    PYTHON := python3
endif

PYTHON_PATH := $(shell $(PYTHON) -c "import sys;print(sys.exec_prefix)")

build-dll-windows:
	gcc image_viewer/c_extensions/os_util_nt.c -L$(PYTHON_PATH)/libs/ -I$(PYTHON_PATH)/include/ -lpython312 -O3 -s -shared -o image_viewer/dll/os_util_nt.dll -Wall -Werror

install:
	$(PYTHON) compile.py --standalone --strip --no-cleanup
