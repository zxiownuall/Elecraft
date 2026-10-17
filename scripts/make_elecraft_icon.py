#!/usr/bin/env python3
"""Draw Elecraft's independent geometric E without image libraries or upstream assets."""
from pathlib import Path
import struct
import zlib

SIZE = 256
BACKGROUND = (16, 36, 65)
FOREGROUND = (230, 245, 255)


def chunk(tag: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))


def make_png() -> bytes:
    # Three bars and a stem, with no raster input from any other project.
    rectangles = ((54, 54, 78, 202), (76, 54, 202, 80),
                  (76, 114, 177, 140), (76, 176, 202, 202))
    rows = bytearray()
    for y in range(SIZE):
        rows.append(0)  # PNG filter: none
        for x in range(SIZE):
            rows.extend(FOREGROUND if any(x0 <= x < x1 and y0 <= y < y1 for x0, y0, x1, y1 in rectangles) else BACKGROUND)
    ihdr = struct.pack(">IIBBBBB", SIZE, SIZE, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(bytes(rows), 9)) + chunk(b"IEND", b"")


def main() -> None:
    directory = Path(__file__).resolve().parents[1] / "assets/app-icon"
    directory.mkdir(parents=True, exist_ok=True)
    png = make_png()
    (directory / "elecraft-256.png").write_bytes(png)
    header = struct.pack('<HHH', 0, 1, 1) + struct.pack('<BBBBHHII', 0, 0, 0, 0, 1, 32, len(png), 22)
    (directory / "elecraft.ico").write_bytes(header + png)


if __name__ == '__main__':
    main()
