#define INITGUID
#define PY_SSIZE_T_CLEAN

#include <fileapi.h>
#include <oleauto.h>
#include <Python.h>
#include <shlguid.h>
#include <shlwapi.h>
#include <windows.h>
#include "b64/cencode.h"

#ifdef __MINGW32__
#include <shlobj.h>
#else
#include <shlobj_core.h>
#endif

/**
 * Given some data, opens, emptys, sets, and closes clipboard
 * with provided data.
 *
 * Returns WINBOOL if successful. If it fails, call GetLastError for information.
 */
static WINBOOL set_win_clipboard(const HWND hwnd, const UINT format, void *data)
{
    return !OpenClipboard(hwnd) || !EmptyClipboard() || !SetClipboardData(format, data) || !CloseClipboard();
}

/**
 * Copies string into a newly allocated buffer, replaces all
 * forward slashes with backslashes, and double null terminates it.
 *
 * Caller must free this string.
 */
static char *normalize_str_for_file_op(const char *str)
{
    int i = 0;
    char *buffer = (char *)malloc((strlen(str) + 2) * sizeof(char));

    for (; str[i] != '\0'; i++)
    {
        buffer[i] = str[i] == '/' ? '\\' : str[i];
    }
    buffer[i++] = '\0';
    buffer[i] = '\0';

    return buffer;
}

/**
 * Adds another null terminator to a string.
 *
 * Caller responsible for ensuring provided string has enough space for one additional char.
 */
static void ensure_double_null_terminated(char *str)
{
    size_t strLen = strlen(str);
    str[strLen + 1] = '\0';
}

static PyObject *trash_file(PyObject *self, PyObject *args)
{
    HWND hwnd;
    const char *pathRaw;

    if (!PyArg_ParseTuple(args, "is", &hwnd, &pathRaw))
    {
        return NULL;
    }

    Py_BEGIN_ALLOW_THREADS;

    char *path = normalize_str_for_file_op(pathRaw);

    SHFILEOPSTRUCTA fileOp = {hwnd, FO_DELETE, path, NULL, FOF_ALLOWUNDO | FOF_FILESONLY | FOF_NOCONFIRMATION | FOF_NOERRORUI};
    SHFileOperationA(&fileOp);

    free(path);

    Py_END_ALLOW_THREADS;

    return Py_None;
}

static PyObject *restore_file(PyObject *self, PyObject *args)
{
    HWND hwnd;
    const char *originalPathRaw;

    if (!PyArg_ParseTuple(args, "is", &hwnd, &originalPathRaw))
    {
        return NULL;
    }

    Py_BEGIN_ALLOW_THREADS;

    HRESULT hr;

    CoInitializeEx(NULL, COINIT_APARTMENTTHREADED);

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
    hr = recycleBinFolder->lpVtbl->EnumObjects(recycleBinFolder, hwnd, SHCONTF_NONFOLDERS, &recycleBinIterator);
    if (FAILED(hr))
    {
        goto fail_enum;
    }

    char *originalPath = normalize_str_for_file_op(originalPathRaw);
    char *targetToRestore = NULL;
    DATE targetRecycledTime = 0;

    LPITEMIDLIST pidlItem;
    while (recycleBinIterator->lpVtbl->Next(recycleBinIterator, 1, &pidlItem, NULL) == S_OK)
    {
        STRRET displayName;

        hr = recycleBinFolder->lpVtbl->GetDisplayNameOf(recycleBinFolder, pidlItem, SHGDN_INFOLDER, &displayName);
        if (FAILED(hr))
        {
            CoTaskMemFree(pidlItem);
            continue;
        }

        char displayNameBuffer[MAX_PATH];
        if (StrRetToBufA(&displayName, pidlItem, displayNameBuffer, MAX_PATH) != S_OK)
        {
            CoTaskMemFree(pidlItem);
            continue;
        }

        VARIANT variant;
        const PROPERTYKEY PKey_DisplacedFrom = {FMTID_Displaced, PID_DISPLACED_FROM};
        hr = recycleBinFolder->lpVtbl->GetDetailsEx(recycleBinFolder, pidlItem, &PKey_DisplacedFrom, &variant);
        if (FAILED(hr))
        {
            CoTaskMemFree(pidlItem);
            continue;
        }

        UINT bufferLength = SysStringLen(variant.bstrVal) + strlen(displayNameBuffer) + 2;
        char deletedFileOriginalPath[bufferLength];
        SHUnicodeToTChar(variant.bstrVal, deletedFileOriginalPath, ARRAYSIZE(deletedFileOriginalPath));
        strcat(deletedFileOriginalPath, "\\");
        strcat(deletedFileOriginalPath, displayNameBuffer);

        if (strcmp(originalPath, deletedFileOriginalPath))
        {
            CoTaskMemFree(pidlItem);
            continue;
        }

        const PROPERTYKEY PKey_DisplacedDate = {FMTID_Displaced, PID_DISPLACED_DATE};
        hr = recycleBinFolder->lpVtbl->GetDetailsEx(recycleBinFolder, pidlItem, &PKey_DisplacedDate, &variant);
        if (FAILED(hr))
        {
            CoTaskMemFree(pidlItem);
            continue;
        }

        const DATE recycledTime = variant.date;

        // Restore only the most recently recycled file of this name for consistency
        if (NULL == targetToRestore || targetRecycledTime < recycledTime)
        {
            STRRET binDisplayName;
            hr = recycleBinFolder->lpVtbl->GetDisplayNameOf(recycleBinFolder, pidlItem, SHGDN_FORPARSING, &binDisplayName);
            if (FAILED(hr))
            {
                CoTaskMemFree(pidlItem);
                continue;
            }

            if (NULL != targetToRestore)
            {
                CoTaskMemFree(targetToRestore);
            }

            targetToRestore = CoTaskMemAlloc(MAX_PATH + 1);
            if (StrRetToBufA(&binDisplayName, pidlItem, targetToRestore, MAX_PATH) != S_OK)
            {
                CoTaskMemFree(pidlItem);
                continue;
            }

            ensure_double_null_terminated(targetToRestore);

            targetRecycledTime = recycledTime;
        }

        CoTaskMemFree(pidlItem);
    }

    if (NULL != targetToRestore)
    {
        SHFILEOPSTRUCTA fileOp = {hwnd, FO_MOVE, targetToRestore, originalPath, FOF_RENAMEONCOLLISION | FOF_ALLOWUNDO | FOF_FILESONLY | FOF_NOCONFIRMATION | FOF_NOERRORUI};
        SHFileOperationA(&fileOp);

        CoTaskMemFree(targetToRestore);
    }

    free(originalPath);
fail_enum:
    recycleBinFolder->lpVtbl->Release(recycleBinFolder);
fail_bind:
    ILFree(pidlRecycleBin);
end:
    CoUninitialize();
    Py_END_ALLOW_THREADS;
    return Py_None; // TODO: Could raise OS error for python code to catch
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

    if (!set_win_clipboard(hwnd, CF_HDROP, hGlobal))
    {
    error_free_memory:
        GlobalFree(hGlobal);
    }

end:
    Py_END_ALLOW_THREADS;
    return Py_None;
}

static PyObject *convert_file_to_base64_and_save_to_clipboard(PyObject *self, PyObject *arg)
{
    const char *path = PyUnicode_AsUTF8(arg);
    if (path == NULL)
    {
        return NULL;
    }

    const HANDLE fileAccess = CreateFileA(path, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (fileAccess == INVALID_HANDLE_VALUE)
    {
        return Py_None;
    }

    LARGE_INTEGER fileSizeContainer;
    if (!GetFileSizeEx(fileAccess, &fileSizeContainer))
    {
        return Py_None;
    }
    const ULONGLONG fileSize = fileSizeContainer.QuadPart;

    HGLOBAL hGlobal = GlobalAlloc(GHND, 2 * fileSize);
    if (hGlobal == NULL)
    {
        return Py_None;
    }

    // encoded data is ~4/3x the size of the original data so make encoded buffer 2x the size.
    base64_encodestate state;
    const int INPUT_BUFFER_SIZE = 65536;
    char inputBuffer[INPUT_BUFFER_SIZE];
    char *encodedBuffer = (char *)GlobalLock(hGlobal);
    char *currentPosition = encodedBuffer;

    if (encodedBuffer == NULL)
    {
        GlobalFree(hGlobal);
        return Py_None;
    }

    base64_init_encodestate(&state);

    DWORD bytesRead;
    while (ReadFile(fileAccess, inputBuffer, INPUT_BUFFER_SIZE, &bytesRead, NULL) && bytesRead > 0)
    {
        currentPosition += base64_encode_block(inputBuffer, (unsigned)bytesRead, currentPosition, &state);
    }

    base64_encode_blockend(encodedBuffer, &state);

    GlobalUnlock(hGlobal);
    CloseHandle(fileAccess);

    set_win_clipboard(0, CF_TEXT, encodedBuffer);

    return Py_None;
}

static PyObject *get_byte_display(PyObject *self, PyObject *arg)
{
    long sizeInBytes = PyLong_AsLong(arg);

    const int kbSize = 1024;

    long sizeInKb = sizeInBytes / kbSize;

    PyObject *pyDisplayStr;

    if (sizeInKb > kbSize)
    {
        double sizeInMb = sizeInKb / ((double)kbSize);
        pyDisplayStr = PyUnicode_FromFormat("%f", sizeInMb);
    }
    else
    {
        pyDisplayStr = PyUnicode_FromFormat("%dkb", sizeInKb);
    }

    return pyDisplayStr;
}

static PyObject *is_hex(PyObject *self, PyObject *arg)
{
    const char *hex = PyUnicode_AsUTF8(arg);

    const size_t hexLen = strlen(hex);

    if (hexLen != 7 || hex[0] != '#')
    {
        return Py_False;
    }

    for (int i = 1; i < 7; ++i)
    {
        if (!isxdigit(hex[i]))
        {
            return Py_False;
        }
    }

    return Py_True;
}

static PyMethodDef os_methods[] = {
    {"is_hex", is_hex, METH_O, NULL},
    {"get_byte_display", get_byte_display, METH_O, NULL},
    {"trash_file", trash_file, METH_VARARGS, NULL},
    {"restore_file", restore_file, METH_VARARGS, NULL},
    {"get_files_in_folder", get_files_in_folder, METH_O, NULL},
    {"open_with", open_with, METH_VARARGS, NULL},
    {"drop_file_to_clipboard", drop_file_to_clipboard, METH_VARARGS, NULL},
    {"convert_file_to_base64_and_save_to_clipboard", convert_file_to_base64_and_save_to_clipboard, METH_O, NULL},
    {NULL, NULL, 0, NULL}};

static struct PyModuleDef os_module = {
    PyModuleDef_HEAD_INIT,
    "_os_nt",
    "Python interface for utility functions written in C",
    -1,
    os_methods};

PyMODINIT_FUNC PyInit__os_nt(void)
{
    return PyModule_Create(&os_module);
}
