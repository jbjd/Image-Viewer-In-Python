"""Validation functions for compilation requirements"""

import os
import warnings
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as get_module_version
from sys import version_info

from nuitka import PythonVersions

MINIMUM_PYTHON_VERSION: tuple[int, int] = (3, 11)


def validate_module_dependencies(is_standalone: bool) -> None:
    """Logs warning if installed packages do not match
    specifications in requirments files and errors if they are
    not installed"""
    with open("requirements.txt", "r", encoding="utf-8") as fp:
        file_raw: str = fp.read().strip()
        entries: list[str] = file_raw.split("\n")
        module_and_versions: list[tuple[str, str]] = []
        for entry in entries:
            module_and_version: tuple[str, str] = tuple(
                entry.split(";")[0].split("==")  # type: ignore
            )
            module_and_versions.append(module_and_version)

    missing_modules: list[str] = []

    for module, requested_version in module_and_versions:
        try:
            installed_version: str = get_module_version(module)

            if requested_version != installed_version:
                warnings.warn(
                    f"Expected {module} version {requested_version} "
                    f"but found version {installed_version}"
                )
        except PackageNotFoundError:
            missing_modules.append(module)

    if is_standalone and len(missing_modules) != 0:
        raise Exception(
            f"Missing module dependencies {missing_modules}\n"
            "Please install them to compile as standalone"
        )


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


def _python_version_tuple_to_str(version: tuple[int, int]) -> str:
    major_version, minor_version = version
    return f"{major_version}.{minor_version}"
