#include <Python.h>
#include <fileapi.h>
#include <windows.h>

#ifdef __MINGW32__
#include <shlobj.h>
#else
#include <shlobj_core.h>
#endif

static PyObject *get_files_in_folder(PyObject *self, PyObject *args)
{
    char *path;

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

static PyObject *open_with(PyObject *self, PyObject *args)
{
    HWND hwnd;
    PyObject *pyPath;

    if (!PyArg_ParseTuple(args, "iU", &hwnd, &pyPath))
    {
        return NULL;
    }

    wchar_t *path = PyUnicode_AsWideCharString(pyPath, 0);
    if (path == NULL)
    {
        return NULL;
    }

    struct _openasinfo openAsInfo = {path, NULL, OAIF_EXEC | OAIF_HIDE_REGISTRATION};
    SHOpenWithDialog(hwnd, &openAsInfo);

    PyMem_Free(path);

    return Py_None;
}

static PyObject *get_byte_display(PyObject *self, PyObject *args)
{
    int sizeInBytes;

    if (!PyArg_ParseTuple(args, "i", &sizeInBytes))
    {
        return NULL;
    }

#ifdef _WIN32
    const int kbSize = 1024;
#else
    const int kbSize = 1000;
#endif

    char *result;
    int sizeInKb = sizeInBytes / kbSize;

    if sizeInKb > 999
    {
        float sizeInMb = sizeInKb / ((float)kbSize)
        sprintf(result, "%.2fmb", sizeInMb);
    }
    else
    {
        sprintf(result, "%dkb", sizeInKb);
    }

    return Py_BuildValue("s", result);
}

static PyMethodDef os_methods[] = {
    {"open_with", open_with, METH_VARARGS, NULL},
    {"get_files_in_folder", get_files_in_folder, METH_VARARGS, NULL},
    {NULL, NULL, 0, NULL}};

static struct PyModuleDef os_module = {
    PyModuleDef_HEAD_INIT,
    "c_os_util",
    "Python interface for utility functions written in C",
    -1,
    os_methods};

PyMODINIT_FUNC PyInit__os(void)
{
    return PyModule_Create(&os_module);
}
