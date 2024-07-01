"""Classes and functions that remove unused code and annotations"""

import ast
import os
import re
from _ast import Name
from glob import glob
from re import sub
from shutil import copyfile

from compile_utils.code_to_skip import (
    classes_to_skip,
    dict_keys_to_skip,
    function_calls_to_skip,
    functions_to_noop,
    functions_to_skip,
    regex_to_apply,
    vars_to_skip,
)
from compile_utils.regex import RegexReplacement

try:
    import autoflake
except ImportError:
    import warnings

    warnings.warn(
        (
            "You do not have the autoflake package installed. "
            "Installing it will allow for a slightly smaller output\n"
        )
    )
    del warnings
    autoflake = None

if os.name == "nt":
    separators = r"[\\/]"
else:
    separators = r"[/]"


class TypeHintRemover(ast._Unparser):  # type: ignore
    """Functions copied from base class, mainly edited to remove type hints"""

    def __init__(self, module_name: str = "") -> None:
        super().__init__()

        self.func_to_skip: set[str] = functions_to_skip[module_name]
        self.vars_to_skip: set[str] = vars_to_skip[module_name]
        self.classes_to_skip: set[str] = classes_to_skip[module_name]
        self.func_calls_to_skip: set[str] = function_calls_to_skip[module_name]
        self.func_to_noop: set[str] = functions_to_noop[module_name]
        self.dict_keys_to_skip: set[str] = dict_keys_to_skip[module_name]

        self.vars_to_skip.add("__author__")

        self.write_annotations_without_value: bool = False

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Disable removing annotations within class vars for safety"""
        if node.name in self.classes_to_skip:
            return

        node.bases = [base for base in node.bases if getattr(base, "id", "") != "ABC"]

        self.write_annotations_without_value = True
        super().visit_ClassDef(node)
        self.write_annotations_without_value = False

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Skips some functions and removes type hints from the rest"""
        if node.name in self.func_to_skip:
            return

        if node.name in self.func_to_noop:
            node.body = [ast.Pass()]
            super().visit_FunctionDef(node)
            return

        argument: ast.arg
        for argument in node.args.args:
            argument.annotation = None
        node.returns = None

        # always ignore inside of function context
        previous_ignore: bool = self.write_annotations_without_value

        self.write_annotations_without_value = False
        super().visit_FunctionDef(node)
        self.write_annotations_without_value = previous_ignore

    def visit_Call(self, node: ast.Call) -> None:
        # Skips warnings.warn() calls
        if self._node_is_logging(node):
            super().visit_Pass(node)
            return
        if (
            getattr(node.func, "attr", "") not in self.func_calls_to_skip
            and getattr(node.func, "id", "") not in self.func_calls_to_skip
        ):
            super().visit_Call(node)

    @staticmethod
    def _node_is_logging(node: ast.Call) -> bool:
        return (
            getattr(node.func, "attr", "") == "warn"
            and getattr(node.func, "value", ast.Name("")).id == "warnings"
        ) or (
            getattr(node.func, "attr", "") == "debug"
            and "log" in getattr(node.func, "value", ast.Name("")).id
        )

    def visit_Assign(self, node: ast.Assign) -> None:
        """Skips over some variables"""
        if getattr(getattr(node.value, "func", object), "attr", "") == "getLogger":
            return

        var_name: str = getattr(node.targets[0], "id", "")
        if var_name not in self.vars_to_skip:
            super().visit_Assign(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Remove var annotations and declares like 'var: type' without an = after"""
        if node.value or self.write_annotations_without_value:
            self.fill()
            with self.delimit_if(
                "(", ")", not node.simple and isinstance(node.target, Name)
            ):
                self.traverse(node.target)
            if node.value:
                self.write(" = ")
                self.traverse(node.value)
            else:
                # Can only reach here if annotation must be kept for formatting a class
                self.write(": ")
                # These might refer to removed things, so make them all something
                placeholder_id: str = '"Any"'
                new_node = ast.Name(id=placeholder_id, ctx=None)  # type: ignore
                self.traverse(new_node)

    def visit_If(self, node: ast.If) -> None:
        """Skip if __name__ == "__main__" blocks"""
        try:
            if node.test.left.id == "__name__":  # type: ignore
                return
        except AttributeError:
            pass
        super().visit_If(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Skip unnecessary futures imports"""
        if node.module == "__future__":
            return

        super().visit_ImportFrom(node)

    def visit_Dict(self, node: ast.Dict) -> None:
        """Replace some dict constants"""
        node.keys = [
            k
            for k in node.keys
            if getattr(k, "value", "") not in self.dict_keys_to_skip
        ]
        super().visit_Dict(node)


def clean_file_and_copy(path: str, new_path: str, module_name: str = "") -> None:
    with open(path, "r", encoding="utf-8") as fp:
        source: str = fp.read()

    if module_name in regex_to_apply:
        regex_and_replacement: set[RegexReplacement] = regex_to_apply[module_name]
        for regex, replacement, flags in regex_and_replacement:
            source = re.sub(regex, replacement, source, flags=flags)

    parsed_source: ast.Module = ast.parse(source)
    contents: str = TypeHintRemover(module_name).visit(
        ast.NodeTransformer().visit(parsed_source)
    )

    if autoflake is not None:
        contents = autoflake.fix_code(
            contents,
            remove_all_unused_imports=True,
            remove_duplicate_keys=True,
            remove_unused_variables=True,
            remove_rhs_for_unused_variables=True,
            ignore_pass_statements=True,
            ignore_pass_after_docstring=True,
        )

    with open(new_path, "w", encoding="utf-8") as fp:
        fp.write(contents)


def move_files_to_tmp_and_clean(
    dir: str, tmp_dir: str, mod_prefix: str, modules_to_skip: list[str] | None = None
) -> None:
    """Moves python files from dir to temp_dir and removes unused/unneeded code"""
    for python_file in iter(
        os.path.abspath(p)
        for p in glob(f"{dir}/**/*", recursive=True)
        if p.endswith((".py", ".pyi", ".pyd"))
    ):
        if os.path.basename(python_file) == "__main__.py" and mod_prefix != "":
            continue  # skip __main__ in modules other than this one

        relative_path: str = os.path.join(
            mod_prefix, python_file.replace(dir, "").strip("/\\")
        )
        new_path: str = os.path.join(tmp_dir, relative_path)
        os.makedirs(os.path.dirname(new_path), exist_ok=True)

        if python_file.endswith(".py"):
            mod_name: str = sub(separators, ".", relative_path)[:-3]  # chops of .py
            if modules_to_skip is None or mod_name not in modules_to_skip:
                clean_file_and_copy(python_file, new_path, mod_name)
        else:
            copyfile(python_file, new_path)
