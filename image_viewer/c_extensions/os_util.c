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
    char *path;

    if (!PyArg_ParseTuple(args, "is", &hwnd, &path))
    {
        return NULL;
    }

    const size_t path_len = strlen(path) + 1;

    wchar_t *wPath = (wchar_t*)malloc(path_len * sizeof(wchar_t));

    if (wPath == NULL) {
        return NULL;
    }

    mbstowcs(wPath, path, path_len);

    struct _openasinfo openAsInfo = {wPath, NULL,  OAIF_EXEC | OAIF_HIDE_REGISTRATION};

    SHOpenWithDialog(hwnd, &openAsInfo);

    free(wPath);

    return Py_None;
}

static PyMethodDef os_util_methods[] = {
    {"open_with", open_with, METH_VARARGS, NULL},
    {"get_files_in_folder", get_files_in_folder, METH_VARARGS, NULL},
    {NULL, NULL, 0, NULL}};

static struct PyModuleDef os_util_module = {
    PyModuleDef_HEAD_INIT,
    "c_os_util",
    "Python interface for utility functions written in C",
    -1,
    os_util_methods};

PyMODINIT_FUNC PyInit_c_os_util(void)
{
    return PyModule_Create(&os_util_module);
}
