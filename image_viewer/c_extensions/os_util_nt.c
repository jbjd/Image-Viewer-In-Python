#include <Python.h>
#include <shlwapi.h>

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

    PyObject *pyFileName;
    do
    {
        if (dirData.dwFileAttributes == FILE_ATTRIBUTE_NORMAL || dirData.dwFileAttributes == FILE_ATTRIBUTE_ARCHIVE)
        {
            pyFileName = Py_BuildValue("u", dirData.cFileName);
            PyList_Append(pyFiles, pyFileName);
        }
    } while (FindNextFileW(fileHandle, &dirData));

    FindClose(fileHandle);

    return pyFiles;
}
