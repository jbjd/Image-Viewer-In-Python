#define PY_SSIZE_T_CLEAN

#include <Python.h>
#include <turbojpeg.h>

// CMemoryViewBuffer Start
typedef struct
{
    PyObject_HEAD;
    char *buffer;
    unsigned long bufferSize;
    PyObject *buffer_view;
} CMemoryViewBuffer;

static PyMemberDef CMemoryViewBuffer_members[] = {
    {"buffer_view", Py_T_OBJECT_EX, offsetof(CMemoryViewBuffer, buffer_view), Py_READONLY, 0},
    {NULL}};

static void CMemoryViewBuffer_dealloc(CMemoryViewBuffer *self)
{
    free(self->buffer);
    Py_XDECREF(self->buffer_view);
    Py_TYPE(self)->tp_free((PyObject *)self);
}

static PyTypeObject CMemoryViewBuffer_Type = {
    .ob_base = PyVarObject_HEAD_INIT(NULL, 0).tp_name = "_jpeg_ext.CMemoryViewBuffer",
    .tp_basicsize = sizeof(CMemoryViewBuffer),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_HAVE_STACKLESS_EXTENSION | Py_TPFLAGS_IMMUTABLETYPE | Py_TPFLAGS_DISALLOW_INSTANTIATION,
    .tp_dealloc = (destructor)CMemoryViewBuffer_dealloc,
    .tp_members = CMemoryViewBuffer_members,
};

static inline CMemoryViewBuffer *CMemoryViewBuffer_New(PyObject *pyMemoryView, char *buffer, unsigned long bufferSize)
{
    CMemoryViewBuffer *cMemoryBuffer = (CMemoryViewBuffer *)PyObject_New(CMemoryViewBuffer, &CMemoryViewBuffer_Type);
    cMemoryBuffer->buffer_view = pyMemoryView;
    cMemoryBuffer->buffer = buffer;
    cMemoryBuffer->bufferSize = bufferSize;

    return cMemoryBuffer;
}
// CMemoryViewBuffer End

// CMemoryViewBufferJpeg End
typedef struct
{
    CMemoryViewBuffer base;
    PyObject *dimensions;
} CMemoryViewBufferJpeg;

static PyMemberDef CMemoryViewBufferJpeg_members[] = {
    {"dimensions", Py_T_OBJECT_EX, offsetof(CMemoryViewBufferJpeg, dimensions), Py_READONLY, 0},
    {NULL}};

static void CMemoryViewBufferJpeg_dealloc(CMemoryViewBufferJpeg *self)
{
    Py_XDECREF(self->dimensions);
    Py_TYPE(self)->tp_free((PyObject *)self);
}

static PyTypeObject CMemoryViewBufferJpeg_Type = {
    .ob_base = PyVarObject_HEAD_INIT(NULL, 0).tp_name = "_jpeg_ext.CMemoryViewBufferJpeg",
    .tp_basicsize = sizeof(CMemoryViewBufferJpeg),
    .tp_itemsize = 0,
    .tp_base = &CMemoryViewBuffer_Type,
    .tp_flags = Py_TPFLAGS_HAVE_STACKLESS_EXTENSION | Py_TPFLAGS_IMMUTABLETYPE | Py_TPFLAGS_DISALLOW_INSTANTIATION,
    .tp_dealloc = (destructor)CMemoryViewBufferJpeg_dealloc,
    .tp_members = CMemoryViewBufferJpeg_members,
};

static inline CMemoryViewBufferJpeg *CMemoryViewBufferJpeg_New(PyObject *pyMemoryView, char *buffer, unsigned long bufferSize, int width, int height)
{
    CMemoryViewBufferJpeg *cMemoryBuffer = (CMemoryViewBufferJpeg *)PyObject_New(CMemoryViewBufferJpeg, &CMemoryViewBufferJpeg_Type);
    cMemoryBuffer->base.buffer_view = pyMemoryView;
    cMemoryBuffer->base.buffer = buffer;
    cMemoryBuffer->base.bufferSize = bufferSize;
    cMemoryBuffer->dimensions = Py_BuildValue("(ii)", width, height);

    return cMemoryBuffer;
}
// CMemoryViewBufferJpeg End

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

    if (size < 0)
    {
        fclose(file);
        goto error;
    }

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

    return (PyObject *)CMemoryViewBuffer_New(pyMemoryView, buffer, size);
error:
    return Py_None;
}

static inline int get_scaled_dimension(int dimension, int numerator, int denominator)
{
    return (dimension * numerator + denominator - 1) / denominator;
}

static PyObject *decode_scaled_jpeg(PyObject *self, PyObject *const *args, Py_ssize_t argLen)
{
    if (argLen != 2)
    {
        PyErr_SetString(PyExc_TypeError, "decode_scaled_jpeg takes exactly two arguments");
        return NULL;
    }

    CMemoryViewBuffer *memoryViewBuffer = (CMemoryViewBuffer *)args[0];

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

    int width, height;
    if (tjDecompressHeader(decompressHandle, (unsigned char *)memoryViewBuffer->buffer, memoryViewBuffer->bufferSize, &width, &height) < 0)
    {
        goto destroy;
    }

    const int pixelFormat = TJPF_RGB;
    const int pixelSize = tjPixelSize[pixelFormat];
    const int scaledWidth = get_scaled_dimension(width, scaledNumerator, scaledDenominator);
    const int scaledHeight = get_scaled_dimension(height, scaledNumerator, scaledDenominator);

    unsigned long resizedJpegBufferSize = scaledWidth * scaledHeight * pixelSize * sizeof(char);
    char *resizedJpegBuffer = (char *)malloc(resizedJpegBufferSize);
    if (resizedJpegBuffer == NULL)
    {
        goto destroy;
    }

    if (tjDecompress2(
            decompressHandle,
            (unsigned char *)memoryViewBuffer->buffer,
            memoryViewBuffer->bufferSize,
            (unsigned char *)resizedJpegBuffer,
            scaledWidth,
            0,
            scaledHeight,
            pixelFormat,
            0) < 0)
    {
        goto destroy;
    }

    PyObject *pyJpegMemoryView = PyMemoryView_FromMemory(resizedJpegBuffer, resizedJpegBufferSize, PyBUF_READ);
    if (pyJpegMemoryView == NULL)
    {
        goto destroy;
    }

    pyReturnValue = (PyObject *)CMemoryViewBufferJpeg_New(pyJpegMemoryView, resizedJpegBuffer, resizedJpegBufferSize, scaledWidth, scaledHeight);

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
    if (PyType_Ready(&CMemoryViewBuffer_Type) < 0 ||
        PyType_Ready(&CMemoryViewBufferJpeg_Type) < 0)
    {
        return NULL;
    }

    PyObject *module = PyModule_Create(&jpeg_module);

    if (PyModule_AddObjectRef(module, "CMemoryViewBuffer", (PyObject *)&CMemoryViewBuffer_Type) < 0 ||
        PyModule_AddObjectRef(module, "CMemoryViewBufferJpeg", (PyObject *)&CMemoryViewBufferJpeg_Type) < 0)
    {
        Py_DECREF(module);
        return NULL;
    }

    return module;
}
