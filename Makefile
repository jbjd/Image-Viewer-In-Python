ifeq ($(OS),Windows_NT)
    PYTHON := python
	PYTHON_PATH := $(shell $(PYTHON) -c "import sys;print(sys.exec_prefix)")
else
    PYTHON := python3
	PYTHON_LIB_PATH := $(subst libpython3.12.so: ,,$(shell whereis libpython3.12.so))
endif

build-os-util:
ifeq ($(OS),Windows_NT)
	gcc image_viewer/c_extensions/util/os_nt.c image_viewer/c_extensions/b64/cencode.c -L$(PYTHON_PATH)/libs/ -I$(PYTHON_PATH)/include/ -Iimage_viewer/c_extensions/ -lpython312 -lshlwapi -loleaut32 -lole32 -O3 -fno-signed-zeros -s -shared -o image_viewer/util/_os_nt.pyd -Wall -Werror
else
	gcc image_viewer/c_extensions/util/os_posix.c image_viewer/c_extensions/b64/cencode.c -L$(PYTHON_LIB_PATH) -I/usr/include/python3.12 -Iimage_viewer/c_extensions/ -lpython3.12 -fPIC -O3 -fno-signed-zeros -s -shared -o image_viewer/util/_os_posix.so -Wall -Werror
endif

install:
	$(PYTHON) compile.py --standalone --strip --no-cleanup

clean:
	rm --preserve-root -Irf __main__.build/ build/ tmp/ *.egg-info/ .coverage compilation-report.xml nuitka-crash-report.xml

test:
	pytest --cov=image_viewer --cov-report term-missing
