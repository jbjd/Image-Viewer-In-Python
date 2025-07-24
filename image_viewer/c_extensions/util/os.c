#define INITGUID
#define PY_SSIZE_T_CLEAN

#include <Python.h>
#include <fileapi.h>
#include <shlwapi.h>
#include <shlguid.h>
#include <windows.h>
#include <oleauto.h>

#ifdef __MINGW32__
#include <shobjidl.h>
#include <shlobj.h>
#else
#include <shobjidl_core.h>
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

    Py_BEGIN_ALLOW_THREADS;

    struct _SHFILEOPSTRUCTA fileOp = {hwnd, FO_DELETE, path, NULL, FOF_ALLOWUNDO | FOF_FILESONLY | FOF_NOCONFIRMATION | FOF_NOERRORUI};
    SHFileOperationA(&fileOp);

    Py_END_ALLOW_THREADS;

    return Py_None;
}

// https://github.com/tribhuwan-kumar/trashbhuwan/blob/be3d00f5916132c6de79271124bd8f6e136cc15e/src/windows/utils.c#L184
static PyObject *restore_file(PyObject *self, PyObject *args)
{
    HWND hwnd;
    const char *original_path;

    if (!PyArg_ParseTuple(args, "is", &hwnd, &original_path))
    {
        return NULL;
    }

    Py_BEGIN_ALLOW_THREADS;

    HRESULT hr;

    // Get recycle bin
    LPITEMIDLIST pidlRecycleBin;
    hr = SHGetSpecialFolderLocation(hwnd, CSIDL_BITBUCKET, &pidlRecycleBin);
    if (FAILED(hr))
    {
        goto end;
    }

    IShellFolder2 *recycleBinFolder = NULL;
    hr = SHBindToObject(NULL, pidlRecycleBin, NULL, &IID_IShellFolder2, (void **)&recycleBinFolder);
    if (FAILED(hr))
    {
        goto fail_bind;
    }

    IEnumIDList *recycleBinIterator = NULL;
    hr = recycleBinFolder->lpVtbl->EnumObjects(recycleBinFolder, NULL, SHCONTF_NONFOLDERS, &recycleBinIterator);
    if (FAILED(hr)) {
        goto fail_enum;
    }

    CoInitialize(0);

    LPITEMIDLIST pidlItem;
    ULONG fetched;
    while (recycleBinIterator->lpVtbl->Next(recycleBinIterator, 1, &pidlItem, &fetched) == S_OK) {
        STRRET displayName;
        char displayNameBuffer[MAX_PATH];

        hr = recycleBinFolder->lpVtbl->GetDisplayNameOf(recycleBinFolder, pidlItem, SHGDN_INFOLDER, &displayName);
        if (SUCCEEDED(hr)) {
            StrRetToBuf(&displayName, pidlItem, displayNameBuffer, MAX_PATH);

            VARIANT variant;
            PROPERTYKEY PKey_DisplacedFrom = { FMTID_Displaced, PID_DISPLACED_FROM };
            recycleBinFolder->lpVtbl->GetDetailsEx(recycleBinFolder, pidlItem, &PKey_DisplacedFrom, &variant);

            UINT bufferLength = SysStringLen(variant.bstrVal);
            char variantBuffer[bufferLength];
            SHUnicodeToTChar(variant.bstrVal, variantBuffer, ARRAYSIZE(variantBuffer));

            printf("%s | %s\\%s\n", original_path, variantBuffer, displayNameBuffer);
        }
        CoTaskMemFree(pidlItem);
    }

    // struct _SHFILEOPSTRUCTA fileOp = {hwnd, FO_MOVE, NULL, original_path, FOF_ALLOWUNDO | FOF_FILESONLY | FOF_NOCONFIRMATION | FOF_NOERRORUI};
    // SHFileOperationA(&fileOp);

    CoUninitialize();
fail_enum:
    recycleBinFolder->lpVtbl->Release(recycleBinFolder);
fail_bind:
    ILFree(pidlRecycleBin);
end:
    Py_END_ALLOW_THREADS;
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
        goto end;
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

end:
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
    {"restore_file", restore_file, METH_VARARGS, NULL},
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
