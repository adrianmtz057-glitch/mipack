"""Lector/escritor NBT mínimo (Java Edition, big-endian) con arrays numpy.

Representación en Python:
  Compound -> dict (orden de inserción preservado)
  List     -> NBTList(tipo, [items])
  Byte/Short/Int/Long/Float/Double -> envoltorios TByte, TShort, ... (subclases de int/float)
  ByteArray/IntArray/LongArray -> np.ndarray de int8/int32/int64
  String   -> str
"""
import gzip
import io
import struct
import zlib

import numpy as np

TAG_END, TAG_BYTE, TAG_SHORT, TAG_INT, TAG_LONG, TAG_FLOAT, TAG_DOUBLE = 0, 1, 2, 3, 4, 5, 6
TAG_BYTE_ARRAY, TAG_STRING, TAG_LIST, TAG_COMPOUND, TAG_INT_ARRAY, TAG_LONG_ARRAY = 7, 8, 9, 10, 11, 12


class TByte(int):
    tag = TAG_BYTE


class TShort(int):
    tag = TAG_SHORT


class TInt(int):
    tag = TAG_INT


class TLong(int):
    tag = TAG_LONG


class TFloat(float):
    tag = TAG_FLOAT


class TDouble(float):
    tag = TAG_DOUBLE


class NBTList(list):
    def __init__(self, tag, items=()):
        super().__init__(items)
        self.tag_type = tag


# ---------------------------------------------------------------- lectura
class _Reader:
    def __init__(self, data):
        self.d = memoryview(data)
        self.p = 0

    def take(self, n):
        v = self.d[self.p:self.p + n]
        self.p += n
        return v

    def u8(self):
        v = self.d[self.p]
        self.p += 1
        return v

    def fmt(self, f, n):
        v = struct.unpack_from(f, self.d, self.p)[0]
        self.p += n
        return v

    def string(self):
        n = self.fmt('>H', 2)
        return bytes(self.take(n)).decode('utf-8', errors='surrogateescape')

    def payload(self, t):
        if t == TAG_BYTE:
            return TByte(self.fmt('>b', 1))
        if t == TAG_SHORT:
            return TShort(self.fmt('>h', 2))
        if t == TAG_INT:
            return TInt(self.fmt('>i', 4))
        if t == TAG_LONG:
            return TLong(self.fmt('>q', 8))
        if t == TAG_FLOAT:
            return TFloat(self.fmt('>f', 4))
        if t == TAG_DOUBLE:
            return TDouble(self.fmt('>d', 8))
        if t == TAG_BYTE_ARRAY:
            n = self.fmt('>i', 4)
            return np.frombuffer(self.take(n), dtype=np.int8).copy()
        if t == TAG_STRING:
            return self.string()
        if t == TAG_LIST:
            et = self.u8()
            n = self.fmt('>i', 4)
            return NBTList(et, [self.payload(et) for _ in range(n)])
        if t == TAG_COMPOUND:
            out = {}
            while True:
                ct = self.u8()
                if ct == TAG_END:
                    return out
                name = self.string()
                out[name] = self.payload(ct)
        if t == TAG_INT_ARRAY:
            n = self.fmt('>i', 4)
            return np.frombuffer(self.take(4 * n), dtype='>i4').astype(np.int32)
        if t == TAG_LONG_ARRAY:
            n = self.fmt('>i', 4)
            return np.frombuffer(self.take(8 * n), dtype='>i8').astype(np.int64)
        raise ValueError(f'tag NBT desconocido {t}')


def loads(data):
    """Decodifica bytes NBT (sin comprimir). Devuelve (nombre_raiz, compound)."""
    r = _Reader(data)
    t = r.u8()
    if t != TAG_COMPOUND:
        raise ValueError('la raíz NBT no es un compound')
    name = r.string()
    return name, r.payload(TAG_COMPOUND)


def load(path):
    raw = open(path, 'rb').read()
    if raw[:2] == b'\x1f\x8b':
        raw = gzip.decompress(raw)
    return loads(raw)


# ---------------------------------------------------------------- escritura
def _tag_of(v):
    if isinstance(v, dict):
        return TAG_COMPOUND
    if isinstance(v, NBTList):
        return TAG_LIST
    t = getattr(v, 'tag', None)
    if t is not None:
        return t
    if isinstance(v, bool):
        return TAG_BYTE
    if isinstance(v, int):
        return TAG_INT
    if isinstance(v, float):
        return TAG_DOUBLE
    if isinstance(v, str):
        return TAG_STRING
    if isinstance(v, np.ndarray):
        if v.dtype == np.int8 or v.dtype == np.uint8:
            return TAG_BYTE_ARRAY
        if v.dtype == np.int32:
            return TAG_INT_ARRAY
        if v.dtype == np.int64:
            return TAG_LONG_ARRAY
        raise TypeError(f'dtype no soportado {v.dtype}')
    if isinstance(v, list):
        raise TypeError('usa NBTList(tipo, items) para listas NBT')
    raise TypeError(f'tipo no soportado {type(v)}')


def _w_string(out, s):
    b = s.encode('utf-8', errors='surrogateescape')
    out.append(struct.pack('>H', len(b)))
    out.append(b)


def _w_payload(out, t, v):
    if t == TAG_BYTE:
        out.append(struct.pack('>b', int(v)))
    elif t == TAG_SHORT:
        out.append(struct.pack('>h', int(v)))
    elif t == TAG_INT:
        out.append(struct.pack('>i', int(v)))
    elif t == TAG_LONG:
        out.append(struct.pack('>q', int(v)))
    elif t == TAG_FLOAT:
        out.append(struct.pack('>f', float(v)))
    elif t == TAG_DOUBLE:
        out.append(struct.pack('>d', float(v)))
    elif t == TAG_BYTE_ARRAY:
        a = np.asarray(v).astype(np.int8)
        out.append(struct.pack('>i', a.size))
        out.append(a.tobytes())
    elif t == TAG_STRING:
        _w_string(out, v)
    elif t == TAG_LIST:
        et = v.tag_type if len(v) else (v.tag_type or TAG_END)
        out.append(struct.pack('>bi', et, len(v)))
        for it in v:
            _w_payload(out, et, it)
    elif t == TAG_COMPOUND:
        for k, it in v.items():
            ct = _tag_of(it)
            out.append(struct.pack('>b', ct))
            _w_string(out, k)
            _w_payload(out, ct, it)
        out.append(b'\x00')
    elif t == TAG_INT_ARRAY:
        a = np.asarray(v).astype('>i4')
        out.append(struct.pack('>i', a.size))
        out.append(a.tobytes())
    elif t == TAG_LONG_ARRAY:
        a = np.asarray(v).astype('>i8')
        out.append(struct.pack('>i', a.size))
        out.append(a.tobytes())
    else:
        raise ValueError(t)


def dumps(compound, name=''):
    out = [b'\x0a']
    _w_string(out, name)
    _w_payload(out, TAG_COMPOUND, compound)
    return b''.join(out)


def save(path, compound, name='', compress=True):
    data = dumps(compound, name)
    if compress:
        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode='wb', mtime=0) as g:
            g.write(data)
        data = buf.getvalue()
    with open(path, 'wb') as f:
        f.write(data)


def zlib_dumps(compound, level=6):
    return zlib.compress(dumps(compound), level)
