#include <Python.h>


static PyObject *is_hex(PyObject *self, PyObject *arg)
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

static PyMethodDef generic_methods[] = {
    {"is_hex", is_hex, METH_O, NULL},
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
