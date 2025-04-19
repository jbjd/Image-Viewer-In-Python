#include <Python.h>
#include <shlwapi.h>

PyObject *create_list(PyObject *py_path)
{
    PyObject *py_list = PyList_New(0);
    if (py_list == NULL)
    {
        return NULL;
    }

    wchar_t *path = PyUnicode_AsWideCharString(py_path, 0);
    if (path == NULL)
    {
        Py_DECREF(py_list);
        return NULL;
    }

    struct _WIN32_FIND_DATAW dirData;
    HANDLE fileHandle = FindFirstFileW(path, &dirData);
    PyMem_Free(path);

    PyObject *py_file_name;
    do
    {
        if (dirData.dwFileAttributes == FILE_ATTRIBUTE_NORMAL || dirData.dwFileAttributes == FILE_ATTRIBUTE_ARCHIVE)
        {
            py_file_name = Py_BuildValue("u", dirData.cFileName);
            PyList_Append(py_list, py_file_name);
        }
    } while (FindNextFileW(fileHandle, &dirData));

    FindClose(fileHandle);

    return py_list;
}
