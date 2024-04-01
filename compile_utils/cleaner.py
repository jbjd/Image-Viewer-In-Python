"""Classes and functions that remove unused code and annotations"""

import ast
import os
from _ast import Name
from glob import glob
from re import sub
from shutil import copyfile

from compile_utils.code_to_skip import (
    classes_to_skip,
    functions_to_skip,
    vars_to_skip,
    function_calls_to_skip,
)

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

    def __init__(self, module_name: str = "", **kwargs) -> None:
        super().__init__(**kwargs)

        self.func_to_skip: set[str] = functions_to_skip[module_name]
        self.vars_to_skip: set[str] = vars_to_skip[module_name]
        self.classes_to_skip: set[str] = classes_to_skip[module_name]
        self.func_calls_to_skip: set[str] = function_calls_to_skip[module_name]

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
        """Removes type hints from functions"""
        if node.name in self.func_to_skip:
            return

        # always ignore inside of function context
        previous_ignore: bool = self.write_annotations_without_value

        self.write_annotations_without_value = False
        super().visit_FunctionDef(node)
        self.write_annotations_without_value = previous_ignore

    def visit_Call(self, node: ast.Call) -> None:
        if (
            getattr(node.func, "attr", "") not in self.func_calls_to_skip
            and getattr(node.func, "id", "") not in self.func_calls_to_skip
        ):
            super().visit_Call(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        """Skips over some variables"""
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
                new_node = ast.Name()
                new_node.ctx = None  # type: ignore
                # These might refer to removed things, so make them all "Any"
                new_node.id = '"Any"'
                self.traverse(new_node)

    def visit_If(self, node: ast.If) -> None:
        """Skip if __name__ == "__main__" blocks"""
        try:
            if node.test.left.id == "__name__":  # type: ignore
                return
        except AttributeError:
            pass
        super().visit_If(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Skip unnecessary futures imports"""
        if node.module == "__future__":
            return

        super().visit_ImportFrom(node)


def clean_file_and_copy(path: str, new_path: str, module_name: str = "") -> None:
    with open(path, "r", encoding="utf-8") as fp:
        parsed_source = ast.parse(fp.read())

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
        )

    with open(new_path, "w", encoding="utf-8") as fp:
        fp.write(contents)


def move_files_to_tmp_and_clean(dir: str, tmp_dir: str, mod_prefix: str) -> None:
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
            clean_file_and_copy(python_file, new_path, mod_name)
        else:
            copyfile(python_file, new_path)
