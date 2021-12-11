from dataclasses import dataclass, field
from io import BytesIO
from typing import List

from isal.igzip import IGzipFile
from isal.isal_zlib import (
    ISAL_BEST_COMPRESSION,
    ISAL_BEST_SPEED,
    ISAL_DEFAULT_COMPRESSION,
)
from isal.isal_zlib import compress as zlib_compress


class CompressionBackend:
    encoding_name: str

    def compress(self, data: bytes, compress_level: int) -> bytes:
        ...


class GzipBackend(CompressionBackend):
    encoding_name = "gzip"

    def compress(self, data: bytes, compress_level: int) -> bytes:
        buffer = BytesIO()
        gzip_file = IGzipFile(mode="wb", fileobj=buffer, compresslevel=compress_level)
        gzip_file.write(data)
        gzip_file.close()
        return buffer.getvalue()


class ZlibBackend(CompressionBackend):
    encoding_name = "deflate"

    def compress(self, data: bytes, compress_level: int) -> bytes:
        return zlib_compress(data, compress_level)


class CompressionLevel:
    BEST_SPEED = ISAL_BEST_SPEED
    AVERAGE_COMPRESSION = ISAL_DEFAULT_COMPRESSION
    BEST_COMPRESSION = ISAL_BEST_COMPRESSION


@dataclass
class Compression:
    level: int = CompressionLevel.BEST_SPEED
    backends: List[CompressionBackend] = field(
        default_factory=lambda: [GzipBackend(), ZlibBackend()]
    )
    minimum_size: int = 1000
