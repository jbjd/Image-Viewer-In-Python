from sys import version_info

try:
    from nuitka import PythonVersions
except ImportError:
    raise ImportError(
        "Nuitka is not installed on your system, it must be installed to compile"
    )


def raise_if_unsupported_python_version() -> None:
    if version_info[:2] < (3, 10):
        raise Exception("Python 3.10 or higher required")

    version: str = f"{version_info[0]}.{version_info[1]}"
    if version in PythonVersions.getNotYetSupportedPythonVersions():
        raise Exception(f"{version} not supported by Nuitka yet")
