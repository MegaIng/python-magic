import encodings
import io
import sys
import tokenize
from abc import ABC, abstractmethod
import codecs
from logging import warn, warning
from typing import Optional, Tuple, List
import re
from string import ascii_lowercase, digits


class FileRewriter(ABC):
    @abstractmethod
    def rewrite(self, s: str) -> str:
        raise NotImplementedError


REWRITER_REGISTER = {}

ALLOWED_CHARS = set(ascii_lowercase + digits)


def register(name: str, rewriter: FileRewriter):
    n = name.lower()
    if not set(n) <= ALLOWED_CHARS:
        raise ValueError(f"{name} is not a valid name. They need to be alphanumeric (no underscore) and ascii")
    if n in REWRITER_REGISTER:
        raise ValueError(f"A rewriter with name {name!r} is already registered")
    REWRITER_REGISTER[n] = rewriter


utf_8 = codecs.lookup('utf_8')


class RewriteCodec(codecs.Codec):
    def __init__(self, rewriters: List[FileRewriter]):
        self.rewriters = rewriters

    def decode(self, inp: bytes, errors: str = "strict") -> Tuple[str, int]:
        inp, con = utf_8.decode(inp)
        if con > 0:
            for r in self.rewriters:
                inp = r.rewrite(inp)
        return inp, con

    def encode(self, inp: str, errors: str = "strict") -> Tuple[bytes, int]:
        inp, con = utf_8.encode(inp)
        return inp, con


def get_incremental(codec: codecs.Codec):
    class IncrementalDecoder(codecs.BufferedIncrementalDecoder):
        def _buffer_decode(self, inp, errors, final):
            if final:
                return codec.decode(inp, errors)
            else:
                return '', 0

    class StreamReader(utf_8.streamreader, object):
        """decode is deferred to support better error messages"""
        _stream = None
        _decoded = False

        @property
        def stream(self):
            if not self._decoded:
                text, _ = codec.decode(self._stream.read())
                self._stream = io.BytesIO(text.encode('UTF-8'))
                self._decoded = True
            return self._stream

        @stream.setter
        def stream(self, stream):
            self._stream = stream
            self._decoded = False

    return IncrementalDecoder, StreamReader


NAME_PATTERN = re.compile(r"rewrite_(\w+(?:_\w+)*)")


def _finder(name: str) -> Optional[codecs.CodecInfo]:
    name = encodings.normalize_encoding(name)
    try:
        m = NAME_PATTERN.match(name.strip())
        if not m:
            return None
        names = m.group(1).split('-')
        rewriters = []
        for n in names:
            if n not in REWRITER_REGISTER:
                try:
                    __import__('rewrite_magic.' + n)
                except ImportError as exc:
                    if exc.name != 'rewrite_magic.' + n:
                        raise
                if n not in REWRITER_REGISTER:
                    warning(f"Unknown rewrite coding {n!r}. We aren't going to do anything.")
                    return None
            rewriters.append(REWRITER_REGISTER[n])
        codec = RewriteCodec(rewriters)
        incdec, strred = get_incremental(codec)
        return codecs.CodecInfo(
            encode=codec.encode,
            decode=codec.decode,
            streamwriter=utf_8.streamwriter,
            streamreader=strred,
            incrementalencoder=utf_8.incrementalencoder,
            incrementaldecoder=incdec,
            name=name
        )
    except Exception:
        sys.excepthook(*sys.exc_info())
        raise
