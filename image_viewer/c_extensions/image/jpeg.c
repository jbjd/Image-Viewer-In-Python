#define PY_SSIZE_T_CLEAN

#include <Python.h>
#include <turbojpeg.h>
#include <stdio.h>

typedef struct
{
    PyObject_HEAD;
    char *buffer;
    PyObject *buffer_view;
} CMemoryViewBuffer;

static PyMemberDef CMemoryViewBuffer_members[] = {
    {"buffer_view", Py_T_OBJECT_EX, offsetof(CMemoryViewBuffer, buffer_view), 0, 0},
    {NULL}};

// static int CMemoryViewBuffer_init(CMemoryViewBuffer *self, PyObject *args, PyObject *kwds) {
//     // Ignore kwds

//     PyObject *pyMemoryView;
//     if (!PyArg_ParseTuple(args, "O", &pyMemoryView)) {
//         return -1;
//     }

//     Py_XINCREF(pyMemoryView);
//     self->buffer_view = pyMemoryView;
//     self->buffer = NULL;  // Must be set by caller

//     return 0;
// }

static void CMemoryViewBuffer_dealloc(CMemoryViewBuffer *self)
{
    printf("dealloc\n");
    free(self->buffer);
    Py_XDECREF(self->buffer_view);
    Py_TYPE(self)->tp_free((PyObject *)self);
}

static PyTypeObject CMemoryViewBuffer_Type = {
    .ob_base = PyVarObject_HEAD_INIT(NULL, 0).tp_name = "_jpeg_ext.CMemoryViewBuffer",
    .tp_basicsize = sizeof(CMemoryViewBuffer),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_HAVE_STACKLESS_EXTENSION | Py_TPFLAGS_IMMUTABLETYPE | Py_TPFLAGS_DISALLOW_INSTANTIATION,
    // .tp_new = PyType_GenericNew,
    // .tp_init = (initproc)CMemoryViewBuffer_init,
    .tp_dealloc = (destructor)CMemoryViewBuffer_dealloc,
    .tp_members = CMemoryViewBuffer_members,
};

static PyObject *read_image_into_buffer(PyObject *self, PyObject *arg)
{
    const char *path = PyUnicode_AsUTF8(arg);
    if (path == NULL)
    {
        return NULL;
    }

    FILE *file = fopen(path, "rb");
    if (file == NULL)
    {
        return Py_None;
    }

    fseek(file, 0, SEEK_END);
    const long size = ftell(file);
    fseek(file, 0, SEEK_SET);

    char *buffer = (char *)malloc(size * sizeof(char));
    if (buffer == NULL)
    {
        fclose(file);
        goto error;
    }

    const size_t readBytes = fread(buffer, sizeof(char), size, file);
    fclose(file);
    if (readBytes != size)
    {
        goto error;
    }

    PyObject *pyMemoryView = PyMemoryView_FromMemory(buffer, size, PyBUF_READ);
    if (pyMemoryView == NULL)
    {
        goto error;
    }

    CMemoryViewBuffer *cMemoryBuffer = (CMemoryViewBuffer*)PyObject_New(CMemoryViewBuffer, &CMemoryViewBuffer_Type);
    cMemoryBuffer->buffer = buffer;
    cMemoryBuffer->buffer_view = pyMemoryView;

    return (PyObject *)cMemoryBuffer;
error:
    return Py_None;
}

static inline int get_scaled_dimension(int dimension, int numerator, int denominator)
{
    return (dimension * numerator + denominator - 1) / denominator;
}

static PyObject *decode_scaled_jpeg(PyObject *self, PyObject *const *args, Py_ssize_t argLen)
{
    if (argLen != 3)
    {
        PyErr_SetString(PyExc_TypeError, "decode_scaled_jpeg takes exactly three arguments");
        return NULL;
    }

    const char *path = PyUnicode_AsUTF8AndSize(args[0], NULL);
    if (path == NULL)
    {
        return NULL;
    }

    int scaledNumerator, scaledDenominator;
    if (!PyArg_ParseTuple(args[1], "ii", &scaledNumerator, &scaledDenominator))
    {
        return NULL;
    }

    PyObject *pyReturnValue = Py_None;

    tjhandle decompressHandle = tjInitDecompress();
    if (decompressHandle == NULL)
    {
        return NULL;
    }

    FILE *jpegFile = fopen(path, "rb");
    if (jpegFile == NULL)
    {
        goto destroy;
    }

    fseek(jpegFile, 0, SEEK_END);
    long jpegSize = ftell(jpegFile);
    fseek(jpegFile, 0, SEEK_SET);

    unsigned char *jpegBuffer = (unsigned char *)malloc(jpegSize * sizeof(unsigned char));
    if (jpegBuffer == NULL)
    {
        fclose(jpegFile);
        goto destroy;
    }

    const size_t readBytes = fread(jpegBuffer, sizeof(char), jpegSize, jpegFile);
    fclose(jpegFile);

    if (readBytes != jpegSize)
    {
        goto free;
    }

    int width, height;
    if (tjDecompressHeader(decompressHandle, jpegBuffer, jpegSize, &width, &height) < 0)
    {
        goto free;
    }

    const int pixelFormat = TJPF_RGB;
    const int pixelSize = tjPixelSize[pixelFormat];
    const int scaledWidth = get_scaled_dimension(width, scaledNumerator, scaledDenominator);
    const int scaledHeight = get_scaled_dimension(height, scaledNumerator, scaledDenominator);

    Py_ssize_t resizedJpegBufferSize = scaledWidth * scaledHeight * pixelSize * sizeof(char);
    char *resizedJpegBuffer = (char *)malloc(resizedJpegBufferSize);
    if (resizedJpegBuffer == NULL)
    {
        goto free;
    }

    if (tjDecompress2(
            decompressHandle,
            jpegBuffer,
            jpegSize,
            (unsigned char *)resizedJpegBuffer,
            scaledWidth,
            0,
            scaledHeight,
            pixelFormat,
            0) < 0)
    {
        goto freeBoth;
    }

    PyObject *pyJpegMemoryView = PyMemoryView_FromMemory(resizedJpegBuffer, resizedJpegBufferSize, PyBUF_READ);
    if (pyJpegMemoryView == NULL)
    {
        goto freeBoth;
    }

    PyObject *pyImageDimensions = Py_BuildValue("(ii)", scaledWidth, scaledHeight);
    if (pyImageDimensions == NULL)
    {
        goto freeMemView;
    }
    PyObject *pyImageArgs = Py_BuildValue("(sOO)", "RGB\0", pyImageDimensions, pyJpegMemoryView);
    if (pyImageArgs == NULL)
    {
        goto freeImageDimensions;
    }

    pyReturnValue = PyObject_CallObject(args[2], pyImageArgs);

    Py_DECREF(pyImageArgs);
freeImageDimensions:
    Py_DECREF(pyImageDimensions);
freeMemView:
    Py_DECREF(pyJpegMemoryView);
freeBoth:
    free(resizedJpegBuffer);
free:
    free(jpegBuffer);
destroy:
    tjDestroy(decompressHandle);
    return pyReturnValue;
}

static PyMethodDef jpeg_methods[] = {
    {"read_image_into_buffer", read_image_into_buffer, METH_O, NULL},
    {"decode_scaled_jpeg", (PyCFunction)decode_scaled_jpeg, METH_FASTCALL, NULL},
    {NULL, NULL, 0, NULL}};

static struct PyModuleDef jpeg_module = {
    PyModuleDef_HEAD_INIT,
    "_jpeg_ext",
    "Python interface for jpeg helper functions written in C",
    -1,
    jpeg_methods};

PyMODINIT_FUNC PyInit__jpeg_ext(void)
{
    if (PyType_Ready(&CMemoryViewBuffer_Type) < 0)
    {
        return NULL;
    }

    PyObject *module = PyModule_Create(&jpeg_module);

    if (PyModule_AddObjectRef(module, "CMemoryViewBuffer", (PyObject *)&CMemoryViewBuffer_Type) < 0)
    {
        Py_DECREF(module);
        return NULL;
    }

    return module;
}
