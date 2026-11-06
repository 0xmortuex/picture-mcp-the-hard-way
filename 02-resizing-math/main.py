"""Module 02: Resizing math - fit, fill, exact, and never upscale by accident.

Run: python main.py
"""

from __future__ import annotations

import os
import tempfile

from PIL import Image


def plan_resize(
    w: int,
    h: int,
    width: int | None = None,
    height: int | None = None,
    percent: float | None = None,
    mode: str = "fit",
    allow_upscale: bool = False,
) -> tuple[tuple[int, int, int, int] | None, tuple[int, int], list[str]]:
    """Pure arithmetic: (crop box or None, final size, notes). No pixels touched.

    Keeping the math separate from Pillow means you can test it with a table of numbers
    instead of generating images.
    """
    notes: list[str] = []
    if mode not in ("fit", "fill", "exact"):
        raise ValueError("mode must be 'fit', 'fill' or 'exact'")
    if percent is not None:
        if width is not None or height is not None:
            raise ValueError("give either percent, or width/height - not both")
        if percent <= 0:
            raise ValueError("percent must be positive")
        if percent > 100 and not allow_upscale:
            raise ValueError("percent > 100 enlarges the image; pass allow_upscale=True")
        return None, (max(1, round(w * percent / 100)), max(1, round(h * percent / 100))), notes
    if width is None and height is None:
        raise ValueError("give width and/or height, or percent")

    if width is None or height is None:  # one side: keep the aspect ratio
        if width is not None:
            tw, th = width, max(1, round(h * width / w))
        else:
            assert height is not None
            tw, th = max(1, round(w * height / h)), height
        if (tw > w or th > h) and not allow_upscale:
            notes.append(f"larger than the source; kept {w}x{h}")
            return None, (w, h), notes
        return None, (tw, th), notes

    if mode == "exact":
        tw, th = width, height
        if not allow_upscale and (tw > w or th > h):
            tw, th = min(tw, w), min(th, h)
            notes.append(f"no upscaling: capped at {tw}x{th}")
        return None, (tw, th), notes

    if mode == "fit":  # largest size INSIDE the box: compare the two ratios
        if width / w <= height / h:
            tw, th = width, max(1, round(h * width / w))
        else:
            tw, th = max(1, round(w * height / h)), height
        if (tw > w or th > h) and not allow_upscale:
            notes.append(f"already fits inside {width}x{height}; kept {w}x{h}")
            return None, (w, h), notes
        return None, (tw, th), notes

    # fill: COVER the box. Crop the source to the box's aspect ratio first, then scale.
    if w / h > width / height:
        ch, cw = h, max(1, min(w, round(h * width / height)))
    else:
        cw, ch = w, max(1, min(h, round(w * height / width)))
    left, top = (w - cw) // 2, (h - ch) // 2
    box = (left, top, left + cw, top + ch)
    if (cw >= width and ch >= height) or allow_upscale:
        return box, (width, height), notes
    notes.append(f"too small to fill {width}x{height} without upscaling; cropped to {cw}x{ch}")
    return box, (cw, ch), notes


def resize_file(src: str, dst: str, **kwargs: object) -> tuple[int, int]:
    with Image.open(src) as im:
        im.load()
        box, size, _ = plan_resize(im.width, im.height, **kwargs)  # type: ignore[arg-type]
        out = im.crop(box) if box else im
        if out.size != size:
            # LANCZOS is the high-quality filter for shrinking. For RGBA, Pillow
            # premultiplies alpha internally so transparent edges do not get dark halos.
            out = out.resize(size, Image.Resampling.LANCZOS)
        out.save(dst)
    return size


def main() -> None:
    # 1. A table of numbers. No images needed.
    table = [
        # w, h, kwargs, expected
        (4000, 3000, {"width": 800}, (800, 600)),
        (4000, 3000, {"height": 600}, (800, 600)),
        (4000, 3000, {"width": 800, "height": 800}, (800, 600)),  # fit: inside the box
        (3000, 4000, {"width": 800, "height": 800}, (600, 800)),
        (4000, 3000, {"percent": 50}, (2000, 1500)),
        (4000, 3000, {"width": 500, "height": 500, "mode": "exact"}, (500, 500)),
        (4000, 3000, {"width": 400, "height": 400, "mode": "fill"}, (400, 400)),
        (100, 50, {"width": 400}, (100, 50)),  # never upscale
        (100, 50, {"width": 400, "allow_upscale": True}, (400, 200)),
        (100, 50, {"width": 300, "height": 300, "mode": "exact"}, (100, 50)),
    ]
    for w, h, kw, expect in table:
        _box, size, _notes = plan_resize(w, h, **kw)  # type: ignore[arg-type]
        assert size == expect, (w, h, kw, size, expect)
    box, size, _ = plan_resize(4000, 3000, width=400, height=400, mode="fill")
    assert box == (500, 0, 3500, 3000), box  # the centered 3000x3000 square
    print("table of", len(table) + 1, "cases passed")

    # 2. Bad requests are errors with a way out, not silent surprises.
    for bad, msg in (({}, "width and/or height"), ({"percent": 150}, "allow_upscale")):
        try:
            plan_resize(100, 100, **bad)
        except ValueError as e:
            assert msg in str(e)
        else:
            raise AssertionError(bad)

    # 3. Real pixels: measure the output files, do not trust the plan.
    work = tempfile.mkdtemp(prefix="pic02-")
    src = os.path.join(work, "wide.png")
    red = Image.linear_gradient("L").rotate(90).resize((300, 100))
    Image.merge("RGB", (red, red, red)).save(src)
    out = os.path.join(work, "fill.png")
    assert resize_file(src, out, width=50, height=50, mode="fill") == (50, 50)
    with Image.open(out) as im:
        assert im.size == (50, 50)
        # fill took the CENTER of a left-to-right gradient: dark on the left, bright on the right
        assert im.getpixel((2, 25))[0] < im.getpixel((47, 25))[0]
        # ...and it is the middle third (about 85..170 of 255), not the whole ramp
        assert 60 < im.getpixel((2, 25))[0] and im.getpixel((47, 25))[0] < 200
    print("fill really cropped the center:", Image.open(out).getpixel((2, 25)))
    print("OK: module 02")


if __name__ == "__main__":
    main()
