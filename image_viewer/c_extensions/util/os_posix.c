#include <sys/stat.h>
#include <Python.h>

#include "b64/cencode.h"

static PyObject *convert_file_to_base64_and_save_to_clipboard(PyObject *self, PyObject *arg)
{
    const char *path = PyUnicode_AsUTF8(arg);
    if (path == NULL)
    {
        return NULL;
    }

    struct stat st;
    stat(path, &st);
    long fileSize = st.st_size;

    FILE *fp = fopen(path, "r");
    if (fp == NULL)
    {
        return Py_None;
    }

    const int INPUT_BUFFER_SIZE = 65536;
    char inputBuffer[INPUT_BUFFER_SIZE];

    int bytesRead = 1;
    while (bytesRead != 0)
    {
        bytesRead = fread(inputBuffer, sizeof(char), INPUT_BUFFER_SIZE, fp);
    }

    fclose(fp);
    return Py_None;
}

static PyMethodDef os_methods[] = {
    {"convert_file_to_base64_and_save_to_clipboard", convert_file_to_base64_and_save_to_clipboard, METH_O, NULL},
    {NULL, NULL, 0, NULL}};

static struct PyModuleDef os_module = {
    PyModuleDef_HEAD_INIT,
    "_os_posix",
    "Python interface for OS utility functions written in C",
    -1,
    os_methods};

PyMODINIT_FUNC PyInit__os_posix(void)
{
    return PyModule_Create(&os_module);
}
