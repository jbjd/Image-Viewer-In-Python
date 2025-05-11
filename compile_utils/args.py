import os
import sys
from argparse import REMAINDER, ArgumentParser, Namespace
from typing import Literal

from compile_utils.validation import raise_if_not_root


class CompileArgumentParser(ArgumentParser):
    """Argument Parser for compilation flags"""

    __slots__ = ()

    VALID_NUITKA_ARGS: set[str] = {
        "--standalone",
        "--quiet",
        "--verbose",
        "--show-scons",
        "--show-memory",
        "--windows-console-mode",
    }

    def __init__(self, install_path: str) -> None:
        super().__init__(
            description="Compiles Personal Image Viewer to an executable",
            epilog=f"Some nuitka arguments are also accepted: {self.VALID_NUITKA_ARGS}",
        )

        default_python: str = "python" if os.name == "nt" else "python3"
        self.add_argument_ext(
            "--python-path",
            "Python to use in compilation, defaults to current interpreter.",
            f"{sys.exec_prefix}/{default_python}",
        )
        self.add_argument_ext(
            "--install-path",
            f"Path to install to, defaults to {install_path}",
            install_path,
        )
        self.add_argument_ext(
            "--report", "Adds --report=compilation-report.xml flag to nuitka."
        )
        self.add_argument_ext(
            "--debug",
            (
                "Doesn't move compiled code to install path, doesn't check for root, "
                "doesn't cleanup, doesn't pass Go, doesn't collect $200, "
                "adds --enable-console, --warn-implicit-exceptions, "
                "--warn-unusual-code, --report=compilation-report.xml flags to nuitka."
            ),
        )
        self.add_argument_ext(
            "--strip",
            (
                "Calls strip on all .exe/.dll/.pyd files after compilation. "
                "Requires strip being installed and on PATH. "
                "This option only works for standalone builds."
            ),
            is_standalone_only=True,
        )
        self.add_argument_ext(
            "--skip-nuitka",
            (
                "Skips running nuitka so no compilation takes place. "
                "Only creates the tmp directory as it would be before compilation."
            ),
            is_debug=True,
        )
        self.add_argument_ext(
            "--no-cleanup",
            "Does not delete temporary files used for compilation/installation.",
            is_debug=True,
        )
        self.add_argument("args", nargs=REMAINDER)

    # for some reason mypy gets the super type wrong
    def parse_known_args(  # type: ignore
        self, imports_to_skip: list[str]
    ) -> tuple[Namespace, list[str]]:
        """Returns Namespace of user arguments and string of args to pass to nuitka"""
        user_args, nuitka_args = super().parse_known_args()
        self._validate_args(nuitka_args, user_args.debug)

        nuitka_args = self._expand_nuitka_args(user_args, nuitka_args, imports_to_skip)

        return user_args, nuitka_args

    def _validate_args(self, nuitka_args: list[str], debug: bool) -> None:
        """Validates root privilege and no unknown arguments present"""
        if not debug:
            raise_if_not_root()

        for extra_arg in nuitka_args:
            if extra_arg.split("=")[0] not in self.VALID_NUITKA_ARGS:
                raise ValueError(f"Unknown argument {extra_arg}")

    @staticmethod
    def _expand_nuitka_args(
        user_args: Namespace, nuitka_args: list[str], imports_to_skip: list[str]
    ) -> list[str]:
        """Given the input list of nuitka args, adds extra arguments
        based on flags user specified"""
        if user_args.report or user_args.debug:
            nuitka_args.append("--report=compilation-report.xml")
            if user_args.debug:
                nuitka_args += ["--warn-implicit-exceptions", "--warn-unusual-code"]

        if not user_args.debug:
            nuitka_args.append("--deployment")

            if not user_args.no_cleanup:
                nuitka_args.append("--remove-output")

        if "--standalone" in nuitka_args:
            nuitka_args.append("--enable-plugin=tk-inter")

            nuitka_args += [
                f"--nofollow-import-to={skipped_import}"
                for skipped_import in imports_to_skip
            ]

        ENABLE_CONSOLE: str = "--windows-console-mode=force"
        DISABLE_CONSOLE: str = "--windows-console-mode=disable"
        ATTACH_CONSOLE: str = "--windows-console-mode=attach"
        if (
            ENABLE_CONSOLE not in nuitka_args
            and DISABLE_CONSOLE not in nuitka_args
            and ATTACH_CONSOLE not in nuitka_args
        ):
            nuitka_args.append(ENABLE_CONSOLE if user_args.debug else DISABLE_CONSOLE)

        return nuitka_args

    def add_argument_ext(
        self,
        name: str,
        help: str,
        default: Literal[False] | str = False,
        is_debug: bool = False,
        is_standalone_only: bool = False,
    ) -> None:
        """Extension of add_argument to simply repeated patterns.
        Adds argument of name with help text. Help text is expanded
        if is_debug or is_standalone_only are True. Infers if argument
        is store or store_true based on passed default."""
        if is_debug:
            help += " This option is exposed for debugging."
        if is_standalone_only:
            help += " This option only works for standalone builds."

        action: str = "store_true" if default is False else "store"

        super().add_argument(name, help=help, action=action, default=default)
