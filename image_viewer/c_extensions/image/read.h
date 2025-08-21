#ifndef PIV_IMAGE_READ
#define PIV_IMAGE_READ

typedef struct
{
    PyObject_HEAD;
    char *buffer;
    unsigned long bufferSize;
    PyObject *view;
} CMemoryViewBuffer;

typedef struct
{
    CMemoryViewBuffer base;
    PyObject *dimensions;
} CMemoryViewBufferJpeg;

#endif /* PIV_IMAGE_READ */
