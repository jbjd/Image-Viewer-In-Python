ifeq ($(OS),Windows_NT)
    PYTHON := python
else
    PYTHON := python3
endif

ifeq ("$(wildcard $(.venv))", "")
    PYTHON_PREFIX := .venv
else
    PYTHON_PREFIX := $(shell $(PYTHON) -c "import sys;print(sys.exec_prefix)")
endif

ifeq ($(OS),Windows_NT)
    PYTHON_PATH := $(PYTHON_PREFIX)/$(PYTHON)
else
    PYTHON_PATH := $(PYTHON_PREFIX)/bin/$(PYTHON)
endif

build-os-util:
	gcc image_viewer/c_extensions/util/os_nt.c image_viewer/c_extensions/b64/cencode.c -L$(PYTHON_PREFIX)/libs/ -I$(PYTHOchoN_PREFIX)/include/ -Iimage_viewer/c_extensions/ -lpython312 -lshlwapi -loleaut32 -lole32 -O3 -fno-signed-zeros -s -shared -o image_viewer/util/_os_nt.pyd -Wall -Werror

install:
	$(PYTHON_PATH) compile.py --standalone --strip --no-cleanup

clean:
	rm --preserve-root -Irf __main__.build/ build/ tmp/ *.egg-info/ .coverage compilation-report.xml nuitka-crash-report.xml

test:
	pytest --cov=image_viewer --cov-report term-missing
