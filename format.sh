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

if [ $mypy_status -ne 0 ]
then
    printf "mypy check failed"
    exit 1
else
    printf "All checks passed"
fi
