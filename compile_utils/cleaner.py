"""Classes and functions that remove unused code and annotations"""

import ast
import os
import re
import subprocess
import warnings
from glob import glob
from re import sub
from typing import Iterator

from personal_compile_tools.file_operations import copy_file, walk_folder
from personal_python_ast_optimizer.flake_wrapper import run_autoflake
from personal_python_ast_optimizer.parser.config import (
    ExtrasConfig,
    SectionsConfig,
    SkipConfig,
    TokensConfig,
)
from personal_python_ast_optimizer.parser.minifier import MinifyUnparser
from personal_python_ast_optimizer.parser.run import run_minify_parser
from personal_python_ast_optimizer.regex.apply import apply_regex, apply_regex_to_file
from personal_python_ast_optimizer.regex.classes import RegexReplacement

from compile_utils.code_to_skip import (
    classes_to_skip,
    constants_to_fold,
    decorators_to_skip,
    dict_keys_to_skip,
    from_imports_to_skip,
    functions_to_skip,
    module_imports_to_skip,
    regex_to_apply_py,
    regex_to_apply_tk,
    vars_to_skip,
)
from compile_utils.package_info import IMAGE_VIEWER_NAME
from compile_utils.validation import get_required_python_version

if os.name == "nt":
    SEPARATORS = r"[\\/]"
else:
    SEPARATORS = r"[/]"


class MinifyUnparserExt(MinifyUnparser):
    """Extends parent to exclude some specific things only relevant to this codebase"""

    __slots__ = ()

    def visit_If(self, node: ast.If) -> None:
        # Skip PIL's blocks about typechecking
        if isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING":
            if node.orelse:
                super().traverse(node.orelse)
            return

        super().visit_If(node)


def clean_file_and_copy(
    path: str, new_path: str, module_name: str, module_import_path: str
) -> None:
    """Given a python file path,
    applies regexes/skips/minification and writes results to new_path"""

    with open(path, "r", encoding="utf-8") as fp:
        source: str = fp.read()

    if module_import_path in regex_to_apply_py:
        regex_replacements: list[RegexReplacement] = regex_to_apply_py.pop(
            module_import_path
        )
        source = apply_regex(source, regex_replacements, module_import_path)

    code_cleaner = MinifyUnparserExt()

    source = run_minify_parser(
        code_cleaner,
        source,
        SkipConfig(
            module_import_path,
            get_required_python_version(),
            constants_to_fold[module_name],
            SectionsConfig(skip_name_equals_main=True),
            _get_tokens_to_skip_config(module_import_path),
            ExtrasConfig(
                fold_constants=False,  # Nuitka does this internally
                skip_overload_functions=True,
            ),
        ),
    )

    source = run_autoflake(source, remove_unused_imports=True)

    with open(new_path, "w", encoding="utf-8") as fp:
        fp.write(source)


def move_files_to_tmp_and_clean(
    source_dir: str,
    tmp_dir: str,
    module_name: str,
    modules_to_skip: set[str] | None = None,
) -> None:
    """Moves python files from source_dir to temp_dir
    and removes unused/unneeded code"""
    if modules_to_skip:
        modules_to_skip_re = rf"^({'|'.join(modules_to_skip)})($|\.)"
    else:
        modules_to_skip_re = ""

    for python_file in _files_in_folder_iter(source_dir, (".py", ".pyd", ".so")):
        if (
            os.path.basename(python_file) == "__main__.py"
            and module_name != IMAGE_VIEWER_NAME
        ):
            continue  # skip __main__ in modules other than this one

        python_file = os.path.abspath(python_file)
        relative_path: str = python_file.replace(source_dir, "").strip("/\\")
        module_import_path: str = sub(SEPARATORS, ".", f"{module_name}.{relative_path}")
        module_import_path = module_import_path[:-3]  # chops .py

        if module_name != IMAGE_VIEWER_NAME:
            relative_path = os.path.join(module_name, relative_path)

        new_path: str = os.path.join(tmp_dir, relative_path)

        if modules_to_skip is not None and (
            skip_match := re.match(modules_to_skip_re, module_import_path)
        ):
            match: str = skip_match.string[: skip_match.end()]
            if match[-1:] == ".":
                match = match[:-1]
            if match in modules_to_skip:
                modules_to_skip.remove(match)
            continue

        os.makedirs(os.path.dirname(new_path), exist_ok=True)
        if python_file.endswith(".py"):
            clean_file_and_copy(python_file, new_path, module_name, module_import_path)
        else:
            copy_file(python_file, new_path)

    if modules_to_skip:
        warnings.warn(
            "Some modules were marked to skip but were not found: "
            + " ".join(modules_to_skip)
        )


def warn_unused_code_skips() -> None:
    """If any values remain from code_to_skip imports, warn
    that they were unused"""
    for skips, friendly_name in (
        (classes_to_skip, "classes"),
        (decorators_to_skip, "decorators"),
        (dict_keys_to_skip, "dictionary Keys"),
        (from_imports_to_skip, "from imports"),
        (module_imports_to_skip, "module imports"),
        (functions_to_skip, "functions"),
        (vars_to_skip, "variables"),
        (regex_to_apply_py, "with regex"),
    ):
        for module in skips:
            warnings.warn(
                f"Asked to skip {friendly_name} in module {module} "
                "but it was not found"
            )


def clean_tk_files(compile_dir: str) -> None:
    """Removes unwanted files that nuitka auto includes in standalone
    and cleans up comments/whitespace from necessary tcl files"""
    for path_or_glob, regexes in regex_to_apply_tk.items():
        glob_result: list[str] = glob(os.path.join(compile_dir, path_or_glob))
        if not glob_result:
            warnings.warn(f"{path_or_glob}: Glob not found")
            continue

        # globs are used since files may have versioning in name
        # They are intended to target a single file
        code_file: str = glob_result[0]
        apply_regex_to_file(code_file, regexes, warning_id=path_or_glob)

    # strip various things in tcl files
    comments = RegexReplacement(pattern=r"^\s*#.*", flags=re.MULTILINE)
    whitespace_around_newlines = RegexReplacement(pattern=r"\n\s+", replacement="\n")
    consecutive_whitespace = RegexReplacement(pattern="[ \t][ \t]+", replacement=" ")
    prints = RegexReplacement(pattern="^(puts|parray) .*", flags=re.MULTILINE)
    extra_new_lines = RegexReplacement(pattern="\n\n+", replacement="\n")
    starting_new_line = RegexReplacement(pattern="^\n", count=1)
    whitespace_between_brackets = RegexReplacement(pattern="}\n}", replacement="}}")

    for code_file in _files_in_folder_iter(compile_dir, (".tcl", ".tm")):
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

    # Had issues adding .so here on linux. Should be revisited here at some point
    for strippable_file in _files_in_folder_iter(compile_dir, (".exe", ".dll", ".pyd")):
        result = subprocess.run(["strip", "--strip-all", strippable_file], check=False)

        if result.returncode != 0:
            warnings.warn(f"Failed to strip file {strippable_file}")


def _get_tokens_to_skip_config(module_import_path: str) -> TokensConfig:
    classes: set[str] | None = classes_to_skip.pop(module_import_path, None)
    decorators: set[str] | None = decorators_to_skip.pop(module_import_path, None)
    dict_keys: set[str] | None = dict_keys_to_skip.pop(module_import_path, None)
    from_imports: set[str] | None = from_imports_to_skip.pop(module_import_path, None)
    module_imports: set[str] | None = module_imports_to_skip.pop(
        module_import_path, None
    )
    functions: set[str] | None = functions_to_skip.pop(module_import_path, None)
    variables: set[str] | None = vars_to_skip.pop(module_import_path, None)

    if functions is not None:
        functions.add("warn")
    else:
        functions = {"warn"}

    return TokensConfig(
        classes_to_skip=classes,
        decorators_to_skip=decorators,
        dict_keys_to_skip=dict_keys,
        from_imports_to_skip=from_imports,
        module_imports_to_skip=module_imports,
        functions_to_skip=functions,
        variables_to_skip=variables,
        no_warn={"warn"},
    )


def _files_in_folder_iter(folder: str, ext_filter: tuple[str, ...]) -> Iterator[str]:
    return iter(p for p in walk_folder(folder) if p.endswith(ext_filter))
