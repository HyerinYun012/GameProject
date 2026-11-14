"""Extract the flattened RGBA cel from the bundled Aseprite character atlas.

The asset pack ships its coloured atlas as an .aseprite file while the PNG is
only a greyscale guide.  This tiny stdlib-only exporter keeps the game free of
runtime image-conversion dependencies.
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path


ASEPRITE_MAGIC = 0xA5E0
FRAME_MAGIC = 0xF1FA
CEL_CHUNK = 0x2005


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    body = kind + payload
    return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body))


def write_rgba_png(path: Path, width: int, height: int, pixels: bytes) -> None:
    rows = b"".join(
        b"\x00" + pixels[y * width * 4 : (y + 1) * width * 4]
        for y in range(height)
    )
    png = (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + _png_chunk(b"IDAT", zlib.compress(rows, 9))
        + _png_chunk(b"IEND", b"")
    )
    path.write_bytes(png)


def alpha_over(dst: bytearray, dst_offset: int, src: bytes, opacity: int) -> None:
    sr, sg, sb, sa = src
    sa = (sa * opacity + 127) // 255
    if sa == 0:
        return
    dr, dg, db, da = dst[dst_offset : dst_offset + 4]
    out_a = sa + (da * (255 - sa) + 127) // 255
    if out_a == 0:
        return
    src_weight = sa * 255
    dst_weight = da * (255 - sa)
    total = src_weight + dst_weight
    dst[dst_offset] = (sr * src_weight + dr * dst_weight + total // 2) // total
    dst[dst_offset + 1] = (sg * src_weight + dg * dst_weight + total // 2) // total
    dst[dst_offset + 2] = (sb * src_weight + db * dst_weight + total // 2) // total
    dst[dst_offset + 3] = out_a


def extract_sheet(source: Path, destination: Path) -> None:
    data = source.read_bytes()
    _, magic, frame_count, canvas_w, canvas_h, depth = struct.unpack_from("<I5H", data, 0)
    if magic != ASEPRITE_MAGIC or depth != 32:
        raise ValueError("Expected a 32-bit RGBA Aseprite file")

    canvas = bytearray(canvas_w * canvas_h * 4)
    frame_offset = 128
    for _ in range(frame_count):
        frame_bytes, frame_magic, old_chunks = struct.unpack_from("<IHH", data, frame_offset)
        if frame_magic != FRAME_MAGIC:
            raise ValueError("Invalid Aseprite frame")
        new_chunks = struct.unpack_from("<I", data, frame_offset + 12)[0]
        chunk_count = new_chunks or old_chunks
        chunk_offset = frame_offset + 16

        for _ in range(chunk_count):
            chunk_size, chunk_type = struct.unpack_from("<IH", data, chunk_offset)
            if chunk_type == CEL_CHUNK:
                _, cel_x, cel_y, opacity, cel_type, _ = struct.unpack_from(
                    "<HhhBHh", data, chunk_offset + 6
                )
                if cel_type not in (0, 2):
                    chunk_offset += chunk_size
                    continue
                image_offset = chunk_offset + 22
                cel_w, cel_h = struct.unpack_from("<HH", data, image_offset)
                payload = data[image_offset + 4 : chunk_offset + chunk_size]
                rgba = payload if cel_type == 0 else zlib.decompress(payload)
                if len(rgba) != cel_w * cel_h * 4:
                    raise ValueError("Unexpected cel payload size")

                for y in range(cel_h):
                    target_y = cel_y + y
                    if not 0 <= target_y < canvas_h:
                        continue
                    for x in range(cel_w):
                        target_x = cel_x + x
                        if not 0 <= target_x < canvas_w:
                            continue
                        src_at = (y * cel_w + x) * 4
                        dst_at = (target_y * canvas_w + target_x) * 4
                        alpha_over(canvas, dst_at, rgba[src_at : src_at + 4], opacity)
            chunk_offset += chunk_size
        frame_offset += frame_bytes

    destination.parent.mkdir(parents=True, exist_ok=True)
    write_rgba_png(destination, canvas_w, canvas_h, bytes(canvas))


def main() -> None:
    project = Path(__file__).resolve().parents[1]
    character_dir = project / "assets" / "Character Creation 32P" / "Character Creation 32P"
    source = character_dir / "Animations.aseprite"
    destination = character_dir / "Animations.png"
    extract_sheet(source, destination)
    print(f"Extracted {destination}")


if __name__ == "__main__":
    main()
