#include <sys/stat.h>
#include <Python.h>
#include <X11/Xlib.h>

#include "b64/cencode.h"

// https://github.com/ColleagueRiley/Clipboard-Copy-Paste/blob/main/x11.c
static void set_x11_clipboard()
{
    Display *display = XOpenDisplay(NULL);

    Window window = XCreateWindow(display, (Window)NULL, 0, 0, 0, 0, 0, 0, InputOnly, NULL, 0 ,NULL);

    // const Atom CLIPBOARD = XInternAtom(display, "CLIPBOARD", False);

    // XConvertSelection(display, CLIPBOARD, XA_STRING, None, window, CurrentTime);
}

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

    // encoded data is ~4/3x the size of the original data so make encoded buffer 2x the size.
    base64_encodestate state;
    const int INPUT_BUFFER_SIZE = 65536;
    char inputBuffer[INPUT_BUFFER_SIZE];
    char *encodedBuffer = (char *)malloc((fileSize * 2) * sizeof(char));
    char *currentPosition = encodedBuffer;

    base64_init_encodestate(&state);

    size_t bytesRead = 1;
    while (bytesRead != 0)
    {
        bytesRead = fread(inputBuffer, sizeof(char), INPUT_BUFFER_SIZE, fp);
        currentPosition += base64_encode_block(inputBuffer, (unsigned)bytesRead, currentPosition, &state);
    }

    base64_encode_blockend(encodedBuffer, &state);

    printf("%s\n", encodedBuffer);

    set_x11_clipboard();

    fclose(fp);
    free(encodedBuffer);

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
