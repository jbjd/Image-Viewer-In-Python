ifeq ($(OS),Windows_NT)
    PYTHON = python
	COMPILED_EXT = pyd
else
    PYTHON = python3
	COMPILED_EXT = so
endif

ifneq (,$(wildcard .venv))  # If .venv folder exists, use that
	ifeq ($(OS),Windows_NT)
		PYTHON_PREFIX = .venv/Scripts
	else
		PYTHON_PREFIX = .venv
	endif
else
    PYTHON_PREFIX := $(shell $(PYTHON) -c "import sys;print(sys.exec_prefix)")
endif

ifeq ($(OS),Windows_NT)
    PYTHON_PATH := $(PYTHON_PREFIX)/$(PYTHON)
else
    PYTHON_PATH := $(PYTHON_PREFIX)/bin/$(PYTHON)
endif

C_SOURCE = image_viewer/c_extensions
C_FLAGS_SHARED = -L$(PYTHON_PREFIX)/libs/ -I$(PYTHON_PREFIX)/include/ -lpython312 -O3 -fno-signed-zeros -s -shared -Wall -Werror

build-util-os-nt:
ifeq ($(OS),Windows_NT)
	gcc $(C_SOURCE)/util/os_nt.c $(C_SOURCE)/b64/cencode.c -I$(C_SOURCE) -lshlwapi -loleaut32 -lole32 $(C_FLAGS_SHARED) -o image_viewer/util/_os_nt.$(COMPILED_EXT)
else
	@echo "Nothing to do for build-util-os-nt:"
endif

build-util-generic:
	gcc $(C_SOURCE)/util/generic.c $(C_FLAGS_SHARED) -o image_viewer/util/_generic.$(COMPILED_EXT)

build-all: build-util-os-nt build-util-generic

install:
	$(PYTHON_PATH) compile.py --standalone --strip --no-cleanup

clean:
	rm --preserve-root -Irf */__pycache__/ *.dist/ *.build/ build/ tmp*/ *.egg-info/ .mypy_cache/ .pytest_cache/ */ERROR.log *.exe .coverage compilation-report.xml nuitka-crash-report.xml

test:
	pytest --cov=image_viewer --cov-report term-missing
