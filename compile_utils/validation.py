"""Validation functions for compilation requirements"""

import os
from sys import version_info

from nuitka import PythonVersions

MINIMUM_PYTHON_VERSION: tuple[int, int] = (3, 11)


def raise_if_unsupported_python_version() -> None:
    if version_info[:2] < MINIMUM_PYTHON_VERSION:
        minimum_supported: str = _python_version_tuple_to_str(MINIMUM_PYTHON_VERSION)
        raise Exception(f"Python {minimum_supported} or higher required")

    version: str = _python_version_tuple_to_str(version_info[:2])
    if version in PythonVersions.getNotYetSupportedPythonVersions():
        raise Exception(f"{version} not supported by Nuitka yet")


def raise_if_not_root() -> None:
    is_root: bool
    if os.name == "nt":
        import ctypes

        is_root = ctypes.windll.shell32.IsUserAnAdmin() != 0  # type: ignore
    else:
        # On windows, mypy complains
        is_root = os.geteuid() == 0  # type: ignore

    if not is_root:
        raise PermissionError("need root privileges to compile and install")


def _python_version_tuple_to_str(version: tuple[int, int]):
    major_version, minor_version = version
    return f"{major_version}.{minor_version}"
