"""Validation functions for compilation requirements"""

import warnings
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as get_module_version
from sys import version_info

from personal_compile_tools.converters import version_tuple_to_str
from personal_compile_tools.requirements import Requirement, parse_requirements_file
from personal_compile_tools.requirement_operators import Operators
from personal_compile_tools.validation import is_root

from nuitka import PythonVersions

MINIMUM_PYTHON_VERSION: tuple[int, int] = (3, 11)


def validate_module_requirements(is_standalone: bool) -> None:
    """Logs warning if installed packages do not match
    specifications in requirements files and errors if they are
    not installed"""
    requirements: list[Requirement] = parse_requirements_file(
        "requirements.txt"
    ) + parse_requirements_file("requirements_compile.txt")

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


def raise_if_unsupported_python_version() -> None:
    if version_info[:2] < MINIMUM_PYTHON_VERSION:
        minimum_supported: str = version_tuple_to_str(MINIMUM_PYTHON_VERSION)
        raise Exception(f"Python {minimum_supported} or higher required")

    version: str = version_tuple_to_str(version_info[:2])
    if version in PythonVersions.getNotYetSupportedPythonVersions():
        raise Exception(f"{version} not supported by Nuitka yet")


def raise_if_not_root() -> None:
    if not is_root():
        raise PermissionError("need root privileges to compile and install")


def _personal_module_matches_installed_version(name: str, source_url: str) -> bool:
    """Returns true if the 'personal' modules from the url are the correct version

    Since they are tagged with their version, we can check if the url ends
    with the version"""
    installed_version: str = get_module_version(name)

    return source_url.endswith(installed_version)
