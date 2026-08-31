"""Regenerates icon.ico from icon.bmp (`python generate_icon.py`, manual -
not part of build.ps1). Crops the non-square source to a square and
hand-writes sharpened per-size frames - Pillow can't do either on its own."""

import struct
from io import BytesIO

from PIL import Image, ImageFilter

SOURCE = "icon.bmp"
OUTPUT = "icon.ico"
SIZES = [16, 24, 32, 48, 64, 96, 128]  # 256 excluded - source can't supply it without upscaling
SHARPEN_MAX_SIZE = 64


def build_frame(source, size):
    frame = source.resize((size, size), Image.LANCZOS)
    if size <= SHARPEN_MAX_SIZE:
        frame = frame.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=2))
    return frame


def write_ico(frames, path):
    offset = 6 + 16 * len(frames)
    entries = []
    blobs = []
    for size, frame in frames:
        buf = BytesIO()
        frame.save(buf, format="PNG")
        data = buf.getvalue()
        blobs.append(data)
        wh = size if size < 256 else 0  # 0 means 256 per the ICO format
        entries.append(struct.pack("<BBBBHHII", wh, wh, 0, 0, 1, 32, len(data), offset))
        offset += len(data)

    with open(path, "wb") as f:
        f.write(struct.pack("<HHH", 0, 1, len(frames)))
        for entry in entries:
            f.write(entry)
        for data in blobs:
            f.write(data)


def main():
    source = Image.open(SOURCE).convert("RGBA")
    square_source = source.crop((0, 0, min(source.size), min(source.size)))
    frames = [(size, build_frame(square_source, size)) for size in SIZES]
    write_ico(frames, OUTPUT)
    print(f"Wrote {OUTPUT} with sizes {SIZES}")


if __name__ == "__main__":
    main()
