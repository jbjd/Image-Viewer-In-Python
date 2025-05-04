#include <Python.h>
#include <fileapi.h>

#define INVALID_HANDLE_VALUE ((HANDLE)(LONG_PTR)-1)

PyObject *get_files_in_folder(PyObject *pyPath)
{
    PyObject *pyFiles = PyList_New(0);
    if (pyFiles == NULL)
    {
        return NULL;
    }

    wchar_t *path = PyUnicode_AsWideCharString(pyPath, 0);
    if (path == NULL)
    {
        Py_DECREF(pyFiles);
        return NULL;
    }

    struct _WIN32_FIND_DATAW dirData;
    HANDLE fileHandle = FindFirstFileW(path, &dirData);
    PyMem_Free(path);

    if (fileHandle == INVALID_HANDLE_VALUE)
	{
        goto finish;
    }

    do
    {
        if ((dirData.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) == 0)
        {
            PyObject *pyFileName = Py_BuildValue("u", dirData.cFileName);
            PyList_Append(pyFiles, pyFileName);
            Py_DECREF(pyFileName);
        }
    } while (FindNextFileW(fileHandle, &dirData));

    FindClose(fileHandle);

finish:
    return pyFiles;
}
