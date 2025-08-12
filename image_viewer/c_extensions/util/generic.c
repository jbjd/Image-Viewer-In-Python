#include <Python.h>
#include <tre/tre.h>

static regex_t valid_keybind_regex;
static int compile_valid_keybind_regex = 1;

static PyObject *is_valid_hex_color(PyObject *self, PyObject *arg)
{
    const ssize_t hexLen = PyUnicode_GetLength(arg);

    if (hexLen != 7)
    {
        return Py_False;
    }

    const char *hex = PyUnicode_AsUTF8(arg);

    if (hex[0] != '#')
    {
        return Py_False;
    }

    for (int i = 1; i < 7; ++i)
    {
        if (!isxdigit(hex[i]))
        {
            return Py_False;
        }
    }

    return Py_True;
}

static PyObject *is_valid_keybind(PyObject *self, PyObject *arg)
{
    if (compile_valid_keybind_regex)
    {
        compile_valid_keybind_regex = tre_regcomp(&valid_keybind_regex, "^<((F([1-9]|(1[0-2])))|((Control-)?([a-zA-Z0-9]|minus|equal)))>$", REG_EXTENDED);
        if (compile_valid_keybind_regex != 0)
        {
            // Failed to compile regex
            return NULL;
        }
    }

    const char *keybind = PyUnicode_AsUTF8(arg);

    const int search_result = tre_regexec(&valid_keybind_regex, keybind, 0, NULL, 0);

    return search_result == 0 ? Py_True : Py_False;
}

static PyMethodDef generic_methods[] = {
    {"is_valid_hex_color", is_valid_hex_color, METH_O, NULL},
    {"is_valid_keybind", is_valid_keybind, METH_O, NULL},
    {NULL, NULL, 0, NULL}};

static struct PyModuleDef generic_module = {
    PyModuleDef_HEAD_INIT,
    "_generic",
    "Python interface for generic utility functions written in C",
    -1,
    generic_methods};

PyMODINIT_FUNC PyInit__generic(void)
{
    return PyModule_Create(&generic_module);
}
