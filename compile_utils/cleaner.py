"""Classes and functions that remove unused code and annotations"""

import ast
import os
import re
import subprocess
import warnings
from glob import glob
from re import sub
from shutil import copyfile

from personal_python_minifier.factories.minifier_factory import ExclusionMinifierFactory
from personal_python_minifier.flake_wrapper import run_autoflake
from personal_python_minifier.parser import parse_source_to_module_node
from personal_python_minifier.parser.config import (
    SectionsToSkipConfig,
    TokensToSkipConfig,
)
from personal_python_minifier.parser.minifier import MinifyUnparser
from personal_python_minifier.regex import RegexReplacement
from personal_python_minifier.regex.apply import apply_regex, apply_regex_to_file

from compile_utils.code_to_skip import (
    classes_to_skip,
    decorators_to_skip,
    dict_keys_to_skip,
    from_imports_to_skip,
    functions_to_skip,
    regex_to_apply_py,
    regex_to_apply_tk,
    vars_to_skip,
)
from compile_utils.validation import MINIMUM_PYTHON_VERSION

if os.name == "nt":
    separators = r"[\\/]"
else:
    separators = r"[/]"


class ExclusionUnparser(MinifyUnparser):
    """Extends parent to exclude specific things only relevant to this codebase"""

    def __init__(self, module_name: str = "") -> None:
        super().__init__(
            module_name=module_name, target_python_version=MINIMUM_PYTHON_VERSION
        )

    def visit_Call(self, node: ast.Call) -> None:
        if self._node_is_warn(node):
            self.visit_Pass(ast.Pass())
            return

        super().visit_Call(node)

    @staticmethod
    def _node_is_warn(node: ast.Call) -> bool:
        return (
            getattr(node.func, "attr", "") == "warn"
            and getattr(node.func, "value", ast.Name("")).id == "warnings"
        )

    def visit_If(self, node: ast.If) -> None:
        # Skip PIL's blocks about typechecking
        if isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING":
            if node.orelse:
                super().traverse(node.orelse)
            return

        super().visit_If(node)


def clean_file_and_copy(path: str, new_path: str, module_name: str = "") -> None:
    with open(path, "r", encoding="utf-8") as fp:
        source: str = fp.read()

    if module_name in regex_to_apply_py:
        regex_replacements: list[RegexReplacement] = regex_to_apply_py[module_name]
        source = apply_regex(source, regex_replacements, module_name)

    code_cleaner: ExclusionUnparser = ExclusionUnparser(module_name)
    code_cleaner = ExclusionMinifierFactory.create_minify_unparser_with_exclusions(
        code_cleaner,
        SectionsToSkipConfig(skip_name_equals_main=True),
        TokensToSkipConfig(
            classes=classes_to_skip[module_name],
            decorators=decorators_to_skip[module_name],
            dict_keys=dict_keys_to_skip[module_name],
            from_imports=from_imports_to_skip[module_name],
            functions=functions_to_skip[module_name],
            variables=vars_to_skip[module_name],
        ),
    )
    source = code_cleaner.visit(parse_source_to_module_node(source))

    edit_imports: bool = module_name[:5] != "numpy"
    source = run_autoflake(source, remove_unused_imports=edit_imports)

    with open(new_path, "w", encoding="utf-8") as fp:
        fp.write(source)


def move_files_to_tmp_and_clean(
    dir: str, tmp_dir: str, mod_prefix: str, modules_to_skip: set[str] | None = None
) -> None:
    """Moves python files from dir to temp_dir and removes unused/unneeded code"""
    if modules_to_skip:
        modules_to_skip_re = rf"^({'|'.join(modules_to_skip)})($|\.)"
    else:
        modules_to_skip_re = ""

    for python_file in iter(
        os.path.abspath(p)
        for p in glob(f"{dir}/**/*", recursive=True)
        if p.endswith((".py", ".pyd"))
    ):
        if os.path.basename(python_file) == "__main__.py" and mod_prefix != "":
            continue  # skip __main__ in modules other than this one

        relative_path: str = os.path.join(
            mod_prefix, python_file.replace(dir, "").strip("/\\")
        )
        new_path: str = os.path.join(tmp_dir, relative_path)
        dir_path: str = os.path.dirname(new_path)

        mod_name: str = sub(separators, ".", relative_path)[:-3]  # chops .py

        if modules_to_skip is not None and (
            skip_match := re.match(modules_to_skip_re, mod_name)
        ):
            match: str = skip_match.string[: skip_match.end()]
            if match[-1] == ".":
                match = match[:-1]
            if match in modules_to_skip:
                modules_to_skip.remove(match)
            continue

        os.makedirs(dir_path, exist_ok=True)
        if python_file.endswith(".py"):
            clean_file_and_copy(python_file, new_path, mod_name)
        else:
            copyfile(python_file, new_path)

    if modules_to_skip:
        warnings.warn(
            "Some imports where marked to skip but not found: "
            + " ".join(modules_to_skip)
        )


def clean_tk_files(compile_dir: str) -> None:
    """Removes unwanted files that nuitka auto includes in standalone
    and cleans up comments/whitespace from necessary tcl files"""
    for path_or_glob, regexs in regex_to_apply_tk.items():
        glob_result: list[str] = glob(os.path.join(compile_dir, path_or_glob))
        if not glob_result:
            warnings.warn(f"{path_or_glob}: Glob not found")
            continue

        # globs are used since files may have versioning in name
        # They are intended to target a single file
        code_file: str = glob_result[0]
        apply_regex_to_file(code_file, regexs, warning_id=path_or_glob)

    # strip various things in tcl files
    comments = RegexReplacement(pattern=r"^\s*#.*", flags=re.MULTILINE)
    whitespace_around_newlines = RegexReplacement(pattern=r"\n\s+", replacement="\n")
    consecutive_whitespace = RegexReplacement(pattern="[ \t][ \t]+", replacement=" ")
    prints = RegexReplacement(pattern="^(puts|parray) .*", flags=re.MULTILINE)
    extra_new_lines = RegexReplacement(pattern="\n\n+", replacement="\n")
    starting_new_line = RegexReplacement(pattern="^\n", count=1)
    whitespace_between_brackets = RegexReplacement(pattern="}\n}", replacement="}}")

    for code_file in glob(os.path.join(compile_dir, "**/*.tcl"), recursive=True) + glob(
        os.path.join(compile_dir, "**/*.tm"), recursive=True
    ):
        apply_regex_to_file(
            code_file,
            [
                comments,
                whitespace_around_newlines,
                consecutive_whitespace,
                prints,
                extra_new_lines,
                starting_new_line,
                whitespace_between_brackets,
            ],
        )

    apply_regex_to_file(
        os.path.join(compile_dir, "tcl/tclIndex"),
        whitespace_around_newlines,
        warning_id="tclIndex",
    )


def strip_files(compile_dir: str) -> None:
    """Runs strip on all exe/dll files in provided dir"""
    EXIT_SUCCESS: int = 0

    strippable_files: list[str] = glob(
        os.path.join(compile_dir, "**/*.exe"), recursive=True
    ) + glob(os.path.join(compile_dir, "**/*.dll"), recursive=True)

    for strippable_file in strippable_files:
        result = subprocess.run(["strip", "--strip-unneeded", strippable_file])

        if result.returncode != EXIT_SUCCESS:
            warnings.warn(f"Failed to strip file {strippable_file}")
