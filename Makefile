ifeq ($(OS),Windows_NT)
    PYTHON := python
else
    PYTHON := python3
endif

PYTHON_PATH := $(shell $(PYTHON) -c "import sys;print(sys.exec_prefix)")

build-dll:
	gcc image_viewer/c_extensions/util/os.c -L$(PYTHON_PATH)/libs/ -I$(PYTHON_PATH)/include/ -lpython312 -lshlwapi -lole32 -O3 -fno-signed-zeros -s -shared -o image_viewer/util/_os.pyd -Wall -Werror

install:
	$(PYTHON) compile.py --standalone --strip --no-cleanup

clean:
	rm --preserve-root -Irf __main__.build/ build/ tmp/ *.egg-info/ .coverage compilation-report.xml nuitka-crash-report.xml

test:
	pytest --cov=image_viewer --cov-report term-missing
