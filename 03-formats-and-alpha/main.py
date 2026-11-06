"""Module 03: Formats and alpha - flatten transparency, keep animations, say what you did.

Run: python main.py
"""

from __future__ import annotations

import io
import os
import tempfile
from typing import Any

from PIL import Image, ImageColor, ImageDraw

FORMATS = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".webp": "WEBP", ".gif": "GIF",
           ".bmp": "BMP"}
CAN_ANIMATE = {"GIF", "WEBP", "PNG"}


def flatten(im: Image.Image, background: str) -> Image.Image:
    """Alpha -> opaque by compositing onto a solid color (what a viewer would show)."""
    r, g, b = ImageColor.getrgb(background)[:3]
    rgba = im.convert("RGBA")
    base = Image.new("RGBA", rgba.size, (r, g, b, 255))
    return Image.alpha_composite(base, rgba).convert("RGB")


def load_frames(path: str) -> tuple[list[Image.Image], list[int]]:
    """Every frame (as RGBA so frames can be mixed) plus per-frame durations in ms."""
    frames, durations = [], []
    with Image.open(path) as im:
        for i in range(getattr(im, "n_frames", 1)):
            im.seek(i)
            im.load()  # WebP only exposes a frame's duration after it is decoded
            durations.append(int(im.info.get("duration", 100) or 100))
            frames.append(im.convert("RGBA"))
    return frames, durations


def convert(src: str, dst: str, background: str = "white") -> list[str]:
    """Convert by the destination's extension. Returns notes: say what you changed."""
    fmt = FORMATS[os.path.splitext(dst)[1].lower()]
    frames, durations = load_frames(src)
    notes: list[str] = []
    if len(frames) > 1 and fmt not in CAN_ANIMATE:
        notes.append(f"animation flattened to its first frame ({fmt} cannot animate)")
        frames, durations = frames[:1], durations[:1]
    if fmt in ("JPEG", "BMP"):
        if any(f.getchannel("A").getextrema()[0] < 255 for f in frames):
            notes.append(f"transparency flattened onto {background}")
        frames = [flatten(f, background) for f in frames]
    kwargs: dict[str, Any] = {}
    if len(frames) > 1:
        kwargs = dict(save_all=True, append_images=frames[1:], duration=durations, loop=0)
        notes.append(f"{len(frames)} animation frames kept")
    frames[0].save(dst, format=fmt, **kwargs)
    return notes


def main() -> None:
    work = tempfile.mkdtemp(prefix="pic03-")

    # 1. The classic bug: transparent PNG -> JPEG gives a BLACK background, because the
    #    hidden RGB under transparent pixels is usually (0, 0, 0).
    png = os.path.join(work, "logo.png")
    logo = Image.new("RGBA", (40, 40), (0, 0, 0, 0))
    logo.paste((255, 0, 0, 255), (0, 0, 20, 40))  # opaque red left half
    logo.save(png)
    naive = io.BytesIO()
    logo.convert("RGB").save(naive, format="JPEG")  # what a careless tool does
    assert Image.open(io.BytesIO(naive.getvalue())).getpixel((30, 20))[0] < 10, "black"
    print("naive RGBA->RGB gives black behind the logo")

    jpg = os.path.join(work, "logo.jpg")
    notes = convert(png, jpg, background="#00ff00")
    with Image.open(jpg) as im:
        r, g, b = im.getpixel((30, 20))
        assert g > 200 and r < 60 and b < 60, (r, g, b)  # transparent area is the green we asked for
        r, g, b = im.getpixel((5, 20))
        assert r > 200 and g < 60  # opaque red stayed red
    assert any("flattened onto #00ff00" in n for n in notes), notes
    print("flattened:", notes)

    # 2. Animated GIF -> WebP keeps every frame and every duration; -> JPEG says it flattened.
    gif = os.path.join(work, "spin.gif")
    imgs = []
    for i in range(5):
        im = Image.new("RGB", (40, 40), "white")
        ImageDraw.Draw(im).rectangle([i * 6, i * 6, i * 6 + 10, i * 6 + 10], fill="red")
        imgs.append(im)
    imgs[0].save(gif, save_all=True, append_images=imgs[1:], duration=120, loop=0)
    webp = os.path.join(work, "spin.webp")
    notes = convert(gif, webp)
    frames, durations = load_frames(webp)
    assert len(frames) == 5 and durations == [120] * 5, (len(frames), durations)
    print("gif -> webp:", notes, durations)
    jpg2 = os.path.join(work, "spin.jpg")
    notes = convert(gif, jpg2)
    assert any("flattened to its first frame" in n for n in notes)
    assert getattr(Image.open(jpg2), "n_frames", 1) == 1
    print("gif -> jpg:", notes)

    # 3. Other modes: palette PNG and CMYK JPEG both need converting before most operations.
    pal = os.path.join(work, "pal.png")
    Image.linear_gradient("L").convert("RGB").quantize(16).save(pal)
    assert Image.open(pal).mode == "P"
    out = os.path.join(work, "pal.jpg")
    convert(pal, out)
    assert Image.open(out).mode == "RGB"
    cmyk = os.path.join(work, "cmyk.jpg")
    Image.new("CMYK", (16, 16), (0, 255, 255, 0)).save(cmyk)  # pure CMYK red
    assert Image.open(cmyk).mode == "CMYK"
    out2 = os.path.join(work, "cmyk.png")
    convert(cmyk, out2)
    r, g, b = Image.open(out2).convert("RGB").getpixel((5, 5))
    assert r > 200 and g < 80 and b < 80, (r, g, b)
    print("palette and CMYK inputs convert to RGB")
    print("OK: module 03")


if __name__ == "__main__":
    main()
