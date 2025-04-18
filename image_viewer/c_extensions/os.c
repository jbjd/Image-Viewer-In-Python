#include <Python.h>
#include <shlwapi.h>

PyObject *create_list(PyObject *path)
{
    PyObject *list = PyList_New(0);
    if (list == NULL)
    {
        return NULL;
    }

    const char *utf8_path = PyUnicode_AsUTF8(path);
    if (utf8_path == NULL)
    {
        return NULL;
    }
    printf("Received UTF-8 string: %s\n", utf8_path);

    struct _WIN32_FIND_DATAA dirData;

    HANDLE fileHandle = FindFirstFileA(utf8_path, &dirData);

    printf("Found: %s\n", dirData.cFileName);
    PyObject *a;

    do
    {
        if (dirData.dwFileAttributes == FILE_ATTRIBUTE_NORMAL || dirData.dwFileAttributes == FILE_ATTRIBUTE_ARCHIVE)
        {
            printf("Found: %s\n", dirData.cFileName);
            a = Py_BuildValue("s", dirData.cFileName);
            PyList_Append(list, a);
        }
    } while (FindNextFileA(fileHandle, &dirData));

    return list;
}
