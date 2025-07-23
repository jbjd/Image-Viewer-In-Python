#define PY_SSIZE_T_CLEAN

#include <Python.h>
#include <fileapi.h>
#include <windows.h>

#ifdef __MINGW32__
#include <shlobj.h>
#else
#include <shlobj_core.h>
#endif

static PyObject *delete_file(PyObject *self, PyObject *args)
{
    HWND hwnd;
    const char *path;

    if (!PyArg_ParseTuple(args, "is", &hwnd, &path))
    {
        return NULL;
    }

    struct _SHFILEOPSTRUCTA fileOp = {hwnd, FO_DELETE, path, NULL, FOF_ALLOWUNDO | FOF_FILESONLY | FOF_NOCONFIRMATION | FOF_NOERRORUI};
    SHFileOperationA(&fileOp);

    return Py_None;
}

static PyObject *get_files_in_folder(PyObject *self, PyObject *arg)
{
    Py_ssize_t pathSize;
    const char *path = PyUnicode_AsUTF8AndSize(arg, &pathSize);
    if (path == NULL)
    {
        return NULL;
    }

    PyObject *pyFiles = PyList_New(0);
    if (pyFiles == NULL)
    {
        return NULL;
    }

    const char pathLastChar = path[pathSize - 1];

    char pathWithStar[pathSize + 3];
    strcpy(pathWithStar, path);

    const char *fuzzySearchEnding = pathLastChar != '/' && pathLastChar != '\\' ? "/*\0" : "*\0";
    strcat(pathWithStar, fuzzySearchEnding);

    struct _WIN32_FIND_DATAA dirData;
    HANDLE fileHandle = FindFirstFileA(pathWithStar, &dirData);

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
    const HWND hwnd;
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

    Py_BEGIN_ALLOW_THREADS;

    const OPENASINFO openAsInfo = {path, NULL, OAIF_EXEC | OAIF_HIDE_REGISTRATION};
    SHOpenWithDialog(hwnd, &openAsInfo);

    Py_END_ALLOW_THREADS;

    PyMem_Free(path);

    return Py_None;
}

static PyObject *drop_file_to_clipboard(PyObject *self, PyObject *args)
{
    const HWND hwnd;
    const char *path;
    Py_ssize_t pathSize;

    if (!PyArg_ParseTuple(args, "is#", &hwnd, &path, &pathSize))
    {
        return NULL;
    }

    Py_BEGIN_ALLOW_THREADS;

    size_t sizeToAlloc = sizeof(DROPFILES) + pathSize + 2;

    HGLOBAL hGlobal = GlobalAlloc(GHND, sizeToAlloc);
    if (hGlobal == NULL)
    {
        goto end;
    }

    DROPFILES *pDropFiles = (DROPFILES *)GlobalLock(hGlobal);
    if (pDropFiles == NULL)
    {
        goto error_free_memory;
    }

    pDropFiles->pFiles = sizeof(DROPFILES);
    pDropFiles->fWide = FALSE;

    char *pathDestination = (char *)((BYTE *)pDropFiles + sizeof(DROPFILES));
    strcpy(pathDestination, path);

    GlobalUnlock(hGlobal);

    if (!OpenClipboard(hwnd))
    {
        goto error_free_memory;
    }

    const int errorDuringSet = !EmptyClipboard() || !SetClipboardData(CF_HDROP, hGlobal);

    CloseClipboard();

    if (errorDuringSet)
    {
        goto error_free_memory;
    }

    goto end;

error_free_memory:
    GlobalFree(hGlobal);
end:
    Py_END_ALLOW_THREADS;
    return Py_None;
}

static PyMethodDef os_methods[] = {
    {"delete_file", delete_file, METH_VARARGS, NULL},
    {"get_files_in_folder", get_files_in_folder, METH_O, NULL},
    {"open_with", open_with, METH_VARARGS, NULL},
    {"drop_file_to_clipboard", drop_file_to_clipboard, METH_VARARGS, NULL},
    {NULL, NULL, 0, NULL}};

static struct PyModuleDef os_module = {
    PyModuleDef_HEAD_INIT,
    "_os",
    "Python interface for utility functions written in C",
    -1,
    os_methods};

PyMODINIT_FUNC PyInit__os(void)
{
    return PyModule_Create(&os_module);
}
