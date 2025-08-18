#define PY_SSIZE_T_CLEAN

#include <Python.h>
#include <turbojpeg.h>

static PyObject *decode_jpeg(PyObject *self, PyObject *const *args, Py_ssize_t argLen)
{
    tjhandle handle = tjInitDecompress();
    if (handle == 0) {
        return 0;
    }

    tjDestroy(handle);

    return Py_None;
}

static PyMethodDef generic_methods[] = {
    {"decode_jpeg", (PyCFunction)decode_jpeg, METH_FASTCALL, NULL},
    {NULL, NULL, 0, NULL}};

static struct PyModuleDef generic_module = {
    PyModuleDef_HEAD_INIT,
    "_jpeg_helper",
    "Python interface for jpeg helper functions written in C",
    -1,
    generic_methods};

PyMODINIT_FUNC PyInit__jpeg_helper(void)
{
    return PyModule_Create(&generic_module);
}
