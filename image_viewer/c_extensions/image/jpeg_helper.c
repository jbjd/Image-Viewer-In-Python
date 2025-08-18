#define PY_SSIZE_T_CLEAN

#include <Python.h>
#include <turbojpeg.h>

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

static PyObject *decode_jpeg(PyObject *self, PyObject *const *args, Py_ssize_t argLen)
{
    tjhandle handle = tjInitDecompress();
    if (handle == 0) {
        return 0;
    }

    //tjDecompressHeader2();

    tjDestroy(handle);

    return PyMemoryView_FromMemory("asdf", 4, PyBUF_WRITE);
}

static PyMethodDef generic_methods[] = {
    {"decode_jpeg", (PyCFunction)decode_jpeg, METH_FASTCALL, NULL},
    {NULL, NULL, 0, NULL}};

static struct PyModuleDef generic_module = {
    PyModuleDef_HEAD_INIT,
    "_jpeg_helper",
    "Python interface for jpeg helper functions written in C",
    -1,
    generic_methods};

PyMODINIT_FUNC PyInit__jpeg_helper(void)
{
    return PyModule_Create(&generic_module);
}
