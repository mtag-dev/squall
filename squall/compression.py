from dataclasses import dataclass, field
from typing import Any, List

from isal.igzip import compress as gzip_compress
from isal.isal_zlib import (
    ISAL_BEST_COMPRESSION,
    ISAL_BEST_SPEED,
    ISAL_DEFAULT_COMPRESSION,
)
from isal.isal_zlib import compress as zlib_compress


class CompressionBackend:
    encoding_name: str

    def compress(self, data: bytes, compress_level: int) -> Any:
        ...


class GzipBackend(CompressionBackend):
    encoding_name = "gzip"

    def compress(self, data: bytes, compress_level: int) -> Any:
        return gzip_compress(data, compress_level)  # type: ignore


class ZlibBackend(CompressionBackend):
    encoding_name = "deflate"

    def compress(self, data: bytes, compress_level: int) -> Any:
        return zlib_compress(data, compress_level)


class CompressionLevel:
    FAST = ISAL_BEST_SPEED
    OPTIMAL = ISAL_DEFAULT_COMPRESSION
    BEST = ISAL_BEST_COMPRESSION


@dataclass
class Compression:
    level: int = CompressionLevel.FAST
    minimum_size: int = 1000

    backends: List[CompressionBackend] = field(
        default_factory=lambda: [GzipBackend(), ZlibBackend()]
    )
