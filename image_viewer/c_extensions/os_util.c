#include <Python.h>
#include <fileapi.h>

#define INVALID_HANDLE_VALUE ((HANDLE)(LONG_PTR) - 1)

static PyObject *get_files_in_folder(PyObject *self, PyObject *args)
{
    const char *path;

    if (!PyArg_ParseTuple(args, "s", &path))
    {
        return NULL;
    }

    PyObject *pyFiles = PyList_New(0);
    if (pyFiles == NULL)
    {
        return NULL;
    }

    struct _WIN32_FIND_DATAA dirData;
    HANDLE fileHandle = FindFirstFileA(path, &dirData);
    //PyMem_Free(path);

    if (fileHandle == INVALID_HANDLE_VALUE)
    {
        goto finish;
    }

    do
    {
        if ((dirData.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) == 0)
        {
            PyObject *pyFileName = Py_BuildValue("s", dirData.cFileName);
            PyList_Append(pyFiles, pyFileName);
            Py_DECREF(pyFileName);
        }
    } while (FindNextFileA(fileHandle, &dirData));

    FindClose(fileHandle);

finish:
    return pyFiles;
}

static PyMethodDef os_util_methods[] = {
    {"get_files_in_folder", get_files_in_folder, METH_VARARGS, NULL},
    {NULL, NULL, 0, NULL}};

static struct PyModuleDef os_util_module = {
    PyModuleDef_HEAD_INIT,
    "c_os_util",
    "Python interface for utility functions written in C",
    -1,
    os_util_methods};

PyMODINIT_FUNC PyInit_c_os_util(void) {
    return PyModule_Create(&os_util_module);
}
