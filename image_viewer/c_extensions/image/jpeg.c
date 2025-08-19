#define PY_SSIZE_T_CLEAN

#include <Python.h>
#include <turbojpeg.h>


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

    // Read JPEG data into the buffer
    fread(jpegBuffer, sizeof(char), jpegSize, jpegFile);
    fclose(jpegFile);

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

    Py_XDECREF(pyImageArgs);
freeImageDimensions:
    Py_XDECREF(pyImageDimensions);
freeMemView:
    Py_XDECREF(pyJpegMemoryView);
freeBoth:
    free(resizedJpegBuffer);
free:
    free(jpegBuffer);
destroy:
    tjDestroy(decompressHandle);
    return pyReturnValue;
}

static PyMethodDef jpeg_methods[] = {
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
    return PyModule_Create(&jpeg_module);
}
