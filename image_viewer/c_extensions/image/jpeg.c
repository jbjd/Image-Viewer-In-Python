#define PY_SSIZE_T_CLEAN

#include <Python.h>
#include <turbojpeg.h>

#include <stdio.h>

/*
int main() {
    // 1. Initialize TurboJPEG decompressor
    tjhandle tjInstance = tjInitDecompress();
    if (tjInstance == NULL) {
        fprintf(stderr, "Error initializing TurboJPEG decompressor: %s\n", tjGetErrorStr2(tjInstance));
        return 1;
    }

    // 2. Load the JPEG image from a file (replace with your file path)
    FILE *jpegFile = fopen("input.jpg", "rb");
    if (jpegFile == NULL) {
        fprintf(stderr, "Error opening input JPEG file.\n");
        tjDestroy(tjInstance);
        return 1;
    }

    // Get the size of the JPEG file
    fseek(jpegFile, 0, SEEK_END);
    long jpegSize = ftell(jpegFile);
    fseek(jpegFile, 0, SEEK_SET);

    // Allocate buffer for JPEG data
    unsigned char *jpegBuf = (unsigned char *)malloc(jpegSize);
    if (jpegBuf == NULL) {
        fprintf(stderr, "Error allocating JPEG buffer.\n");
        fclose(jpegFile);
        tjDestroy(tjInstance);
        return 1;
    }

    // Read JPEG data into the buffer
    fread(jpegBuf, 1, jpegSize, jpegFile);
    fclose(jpegFile);

    // 3. Get JPEG image information (width, height, subsampling, colorspace)
    int width, height, subsamp, colorspace;
    if (tjDecompressHeader2(tjInstance, jpegBuf, jpegSize, &width, &height, &subsamp) < 0) {
        fprintf(stderr, "Error reading JPEG header: %s\n", tjGetErrorStr2(tjInstance));
        free(jpegBuf);
        tjDestroy(tjInstance);
        return 1;
    }

    // 4. Determine output pixel format (e.g., RGB)
    int pixelFormat = TJPF_RGB; // Output as RGB
    int numComponents = tjPixelSize[pixelFormat]; // Number of bytes per pixel

    // 5. Allocate buffer for decompressed image data
    unsigned char *imgBuf = (unsigned char *)malloc(width * height * numComponents);
    if (imgBuf == NULL) {
        fprintf(stderr, "Error allocating image buffer.\n");
        free(jpegBuf);
        tjDestroy(tjInstance);
        return 1;
    }

    // 6. Decompress the JPEG image
    if (tjDecompress2(tjInstance, jpegBuf, jpegSize, imgBuf, width, 0, height, pixelFormat, 0) < 0) {
        fprintf(stderr, "Error decompressing JPEG image: %s\n", tjGetErrorStr2(tjInstance));
        free(jpegBuf);
        free(imgBuf);
        tjDestroy(tjInstance);
        return 1;
    }

    // 7. Process the decompressed image data (e.g., save to a file, display, etc.)
    // For demonstration, we'll just print a message.
    printf("JPEG image successfully decompressed to %dx%d pixels (RGB).\n", width, height);

    // 8. Clean up
    free(jpegBuf);
    free(imgBuf);
    tjDestroy(tjInstance);

    return 0;
}
*/

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
