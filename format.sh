echo "Running isort"
isort .
echo

echo "Running black formatter"
black .
echo

echo "Formatting complete" && echo

echo "Running mypy type checker"
mypy . --check-untyped-defs
mypy_status=$?
echo

echo "Running spell checker"
# using *.py did not work even though codespell docs show it?
codespell image_viewer tests compile_utils compile.py README.md
codespell_status=$?
echo

if [ $mypy_status -ne 0 ] || [ $codespell_status -ne 0 ]
then
    printf "Some checks failed"
    exit 1
else
    printf "All checks passed"
fi
