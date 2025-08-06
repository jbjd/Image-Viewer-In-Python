"""Validation functions for compilation requirements"""

import tomllib
import warnings
from functools import lru_cache
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as get_module_version
from sys import version_info
from typing import Any

from nuitka import PythonVersions
from personal_compile_tools.converters import version_str_to_tuple, version_tuple_to_str
from personal_compile_tools.requirement_operators import Operators
from personal_compile_tools.requirements import Requirement, parse_requirements_file
from personal_compile_tools.validation import is_root

from compile_utils.module_dependencies import module_dependencies
from compile_utils.package_info import PROJECT_FILE


@lru_cache
def get_required_python_version() -> tuple[int, int]:
    """Returns tuple representing the required python version
    by parsing it out of the pyproject.toml file."""

    with open(PROJECT_FILE, "rb") as fp:
        project: dict[str, Any] = tomllib.load(fp)["project"]

    return version_str_to_tuple(project["requires-python"][2:])  # type: ignore


def validate_module_requirements(is_standalone: bool) -> None:
    """Logs warning if installed packages do not match
    specifications in requirements files and errors if they are
    not installed"""
    requirements: list[Requirement] = module_dependencies + parse_requirements_file(
        "requirements_compile.txt"
    )

    missing_modules: list[str] = []

    for requirement in requirements:
        try:
            # personal_compile_tools can't determine direct references,
            # so there is a custom check here
            matches_installed: bool = (
                requirement.matches_installed_version()
                if requirement.rules[0].operator != Operators.DIRECT_REFERENCE
                else _personal_module_matches_installed_version(
                    requirement.name, requirement.rules[0].version.raw_version
                )
            )
            if not matches_installed:
                installed_version: str = get_module_version(requirement.name)
                warnings.warn(
                    f"Expected {requirement} but found version {installed_version}"
                )
        except PackageNotFoundError:
            missing_modules.append(requirement.name)

    if is_standalone and len(missing_modules) != 0:
        raise Exception(
            f"Missing module dependencies {missing_modules}\n"
            "Please install them to compile as standalone"
        )


def validate_python_version() -> None:
    required_python: tuple[int, int] = get_required_python_version()
    used_python: tuple[int, int] = version_info[:2]

    if used_python != required_python:
        warnings.warn(f"Expecting python {required_python} but found {used_python}")

    version: str = version_tuple_to_str(used_python)
    if version in PythonVersions.getNotYetSupportedPythonVersions():
        raise Exception(f"{version} not supported by Nuitka yet")


def raise_if_not_root() -> None:
    """Raises PermissionError if current context isn't root."""
    if not is_root():
        raise PermissionError("need root privileges to compile and install")


def _personal_module_matches_installed_version(name: str, source_url: str) -> bool:
    """Returns true if the 'personal' modules from the url are the correct version

    Since they are tagged with their version, we can check if the url ends
    with the version"""
    installed_version: str = get_module_version(name)

    return source_url.endswith(installed_version)
