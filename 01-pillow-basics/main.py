"""Module 01: Pillow basics - open lazily, decode on purpose, know your modes.

Run: python main.py   (every check is an assert; exit code 0 means the chapter is true)
"""

from __future__ import annotations

import os
import tempfile

from PIL import Image, UnidentifiedImageError


def make_gradient(width: int, height: int) -> Image.Image:
    """Red grows left to right, green grows top to bottom, blue is constant."""
    red = Image.linear_gradient("L").rotate(90).resize((width, height))
    green = Image.linear_gradient("L").resize((width, height))
    blue = Image.new("L", (width, height), 128)
    return Image.merge("RGB", (red, green, blue))


def describe(path: str) -> str:
    """Everything an agent wants to know first, without trusting the file name."""
    try:
        im = Image.open(path)  # reads the header only: cheap even for a 100 MP file
    except UnidentifiedImageError:
        raise ValueError(f"{os.path.basename(path)} is not an image Pillow can read") from None
    with im:
        width, height = im.size
        fmt, mode = im.format, im.mode
        has_alpha = mode in ("RGBA", "LA") or "transparency" in im.info
        try:
            im.load()  # now decode every pixel: this is where truncation shows up
            problem = None
        except OSError as e:
            problem = str(e)
    line = f"{fmt} {width}x{height} {mode} alpha={'yes' if has_alpha else 'no'}"
    return line + (f"  WARNING corrupt/truncated: {problem}" if problem else "")


def main() -> None:
    work = tempfile.mkdtemp(prefix="pic01-")
    src = make_gradient(200, 100)
    assert src.size == (200, 100) and src.mode == "RGB"
    # Pixel (x, y) is a tuple. Gradient check: left is dark red, right is bright red.
    assert src.getpixel((0, 50))[0] < 5 and src.getpixel((199, 50))[0] > 250
    assert src.getpixel((100, 0))[1] < 5 and src.getpixel((100, 99))[1] > 250

    # 1. The same pixels in three formats: sizes differ, pixels (for lossless) do not.
    png, jpg, webp = (os.path.join(work, n) for n in ("g.png", "g.jpg", "g.webp"))
    src.save(png)
    src.save(jpg, quality=90)
    src.save(webp, quality=90)
    sizes = {p: os.path.getsize(p) for p in (png, jpg, webp)}
    print("bytes on disk:", {os.path.basename(p): s for p, s in sizes.items()})
    with Image.open(png) as back:
        assert back.tobytes() == src.tobytes(), "PNG is lossless: identical pixels"
    with Image.open(jpg) as back:
        assert back.tobytes() != src.tobytes(), "JPEG is lossy: pixels changed a little"

    # 2. The format is in the bytes, not the name.
    liar = os.path.join(work, "liar.jpg")
    os.replace(png, liar)  # a PNG pretending to be a JPEG
    with Image.open(liar) as im:
        assert im.format == "PNG"
    print(describe(liar))

    # 3. Open is lazy. A truncated file opens fine and only fails when decoded.
    data = open(jpg, "rb").read()
    cut = os.path.join(work, "cut.jpg")
    open(cut, "wb").write(data[: len(data) // 2])
    with Image.open(cut) as im:
        assert im.size == (200, 100)  # the header is intact, so this "works"
    line = describe(cut)
    assert "WARNING" in line, line
    print(line)

    # 4. Not an image at all.
    junk = os.path.join(work, "junk.png")
    open(junk, "w").write("hello")
    try:
        describe(junk)
    except ValueError as e:
        assert "not an image" in str(e)
        print("junk ->", e)
    else:
        raise AssertionError("junk should have been rejected")

    # 5. Modes decide what can be saved where. JPEG has no alpha channel.
    rgba = Image.new("RGBA", (10, 10), (255, 0, 0, 128))
    try:
        rgba.save(os.path.join(work, "x.jpg"))
    except OSError as e:
        assert "cannot write mode RGBA as JPEG" in str(e)
        print("RGBA -> JPEG:", e)
    else:
        raise AssertionError("expected JPEG to refuse RGBA")
    # Palette, grayscale, CMYK are modes too; convert() moves between them.
    pal = src.quantize(16)
    assert pal.mode == "P" and pal.convert("RGB").mode == "RGB"
    assert src.convert("L").mode == "L"

    print("OK: module 01")


if __name__ == "__main__":
    main()
