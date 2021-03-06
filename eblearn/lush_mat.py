import numpy as np
import struct, sys

MAXDIMS        = 11

BINARY_MATRIX  = 0x1e3d4c51
PACKED_MATRIX  = 0x1e3d4c52
DOUBLE_MATRIX  = 0x1e3d4c53
INTEGER_MATRIX = 0x1e3d4c54
BYTE_MATRIX    = 0x1e3d4c55
SHORT_MATRIX   = 0x1e3d4c56
SHORT8_MATRIX  = 0x1e3d4c57
ASCII_MATRIX   = 0x2e4d4154

swap = lambda x: np.int32(x).byteswap().item()

magic_values = {
    BINARY_MATRIX       : np.dtype(np.float32)
,   PACKED_MATRIX       : np.dtype(np.byte)
,   DOUBLE_MATRIX       : np.dtype(np.float64)
,   INTEGER_MATRIX      : np.dtype(np.int32)
,   BYTE_MATRIX         : np.dtype(np.uint8)
,   SHORT_MATRIX        : np.dtype(np.int16)
,   SHORT8_MATRIX       : np.dtype(np.int8)
,   ASCII_MATRIX        : None
}

def load_matrix_header(f):
    swapflag  = False
    magic, = struct.unpack('=I', f.read(4))
    if swap(magic) in magic_values:
        swapflag = True
        magic = swap(magic)
    if magic not in magic_values:
        raise IOError('Bad matrix format')
    ifmt = '=I'
    if swapflag:
        ifmt = '>I' if sys.byteorder == 'little' else '<I'
    dtype = magic_values[magic]
    if dtype is None:
        raise NotImplementedError('ASCII formats not supported')
    ndim, = struct.unpack(ifmt, f.read(4))
    if ndim == -1: return (None, magic, swapflag)
    if ndim < 0 or ndim > MAXDIMS:
        raise IOError('Bad number of dimensions (%d)' % (ndim,))
    if ndim == 0:  return ((),   magic, swapflag)
    ndim_read = max(ndim, 3)
    shape = struct.unpack(ifmt+('I'*(ndim_read-1)), f.read(4*ndim_read))
    for d in shape[ndim:]:
        if d != 1: raise IOError('Bad matrix format')
    shape = shape[:ndim]
    # -- empty arrays aren't allowed in Lush (doesn't hurt to support them)
    # for d in shape:
    #     if d  < 1: raise IOError('Bad shape: %s' % (shape,))
    return (shape, magic, swapflag)

def save_matrix_header(shape, dtype, f):
    magic = dict([(v.name,k) for (k,v) in magic_values.iteritems()
                  if k not in (ASCII_MATRIX, PACKED_MATRIX,)])[dtype.name]
    ndim  = len(shape)
    shape = list(shape)
    if 0 < len(shape) < 3: shape.extend([1]*(3-len(shape)))
    np.array([magic, ndim]+shape, dtype = 'u4').tofile(f)

def map_matrix(f, mode='c'):
    if type(f) == str: f = open(f, 'r')
    shape, magic, swapflag = load_matrix_header(f)
    dtype  = magic_values[magic]
    offset = f.tell(); f.seek(0)
    return np.memmap(f, dtype, mode, offset, shape)

def load_matrix(f):
    if type(f) == str: f = open(f, 'r')
    shape, magic, swapflag = load_matrix_header(f)
    dtype  = magic_values[magic]
    numels = np.prod(shape, dtype=int)
    return np.fromfile(f, dtype, numels).reshape(shape)

def save_matrix(m, f):
    if type(f) == str: f = open(f, 'w')
    m = np.ascontiguousarray(m)
    save_matrix_header(m.shape, m.dtype, f)
    f.write(m.data)
