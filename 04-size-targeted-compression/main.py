"""Module 04: Size-targeted compression - search for the highest quality that fits.

Run: python main.py
"""

from __future__ import annotations

import io
import math
import os
import random
import tempfile

from PIL import Image


def photo_like(w: int, h: int) -> Image.Image:
    """Noise blown up 4x: detailed enough that JPEG size really depends on quality."""
    rnd = random.Random(7)
    small = Image.frombytes("RGB", (w // 4, h // 4), rnd.randbytes((w // 4) * (h // 4) * 3))
    return small.resize((w, h), Image.Resampling.BICUBIC)


def encode(im: Image.Image, quality: int) -> bytes:
    buf = io.BytesIO()  # encode in memory: no disk I/O inside the search loop
    im.save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue()


def best_quality(im: Image.Image, target: int, lo: int = 30, hi: int = 95) -> tuple[bytes, int] | None:
    """Highest quality in [lo, hi] whose file is <= target bytes, or None if even lo is too big.

    JPEG size grows (almost always) with quality, so binary search works: invariant is
    "a fits, b does not". About log2(65) = 6 encodes instead of 65.
    """
    top = encode(im, hi)
    if len(top) <= target:
        return top, hi
    bottom = encode(im, lo)
    if len(bottom) > target:
        return None
    best, best_q = bottom, lo
    a, b = lo, hi
    while b - a > 1:
        mid = (a + b) // 2
        data = encode(im, mid)
        if len(data) <= target:
            a, best, best_q = mid, data, mid
        else:
            b = mid
    return best, best_q


def compress_to(im: Image.Image, target: int, allow_downscale: bool = False) -> tuple[bytes, str]:
    """Never silently change what the user did not ask to change."""
    scale = 1.0
    for _ in range(8):
        cur = im if scale == 1.0 else im.resize(
            (max(1, round(im.width * scale)), max(1, round(im.height * scale))),
            Image.Resampling.LANCZOS,
        )
        found = best_quality(cur, target)
        if found:
            data, q = found
            return data, f"quality {q}" + (f", downscaled to {cur.width}x{cur.height}" if scale < 1 else "")
        smallest = len(encode(cur, 30))
        if not allow_downscale:
            raise ValueError(
                f"cannot reach {target} bytes: smallest at full size is {smallest}. Raise the "
                "target, lower min quality, or pass allow_downscale=True"
            )
        # Bytes scale roughly with pixel count, so shrink each side by sqrt(target/size).
        scale *= max(0.5, min(0.95, math.sqrt(target / smallest) * 0.95))
    raise ValueError("could not reach the target even after repeated downscaling")


def main() -> None:
    work = tempfile.mkdtemp(prefix="pic04-")
    im = photo_like(1200, 800)

    # 1. Quality vs size is a curve you can measure. It is steep at the top.
    curve = {q: len(encode(im, q)) for q in (30, 50, 70, 85, 95)}
    print("quality -> bytes:", curve)
    assert list(curve.values()) == sorted(curve.values()), "size should grow with quality"

    # 2. Target sizes: measure the FILE on disk, and check we did not waste the budget.
    for kb in (300, 220, 170):
        target = kb * 1024
        data, label = compress_to(im, target)
        path = os.path.join(work, f"t{kb}.jpg")
        open(path, "wb").write(data)
        size = os.path.getsize(path)
        assert size <= target, (size, target)
        assert size > target * 0.7, f"search left too much on the table: {size} of {target}"
        assert Image.open(path).size == (1200, 800)
        print(f"target {kb} KB -> {size / 1024:.1f} KB at {label}")

    # 3. An impossible target is an error with options, not a quietly smaller picture.
    try:
        compress_to(im, 5 * 1024)
    except ValueError as e:
        assert "allow_downscale" in str(e)
        print("impossible target:", e)
    else:
        raise AssertionError("expected an error")

    # 4. ...unless the caller opts in to shrinking pixels, and then it is reported.
    data, label = compress_to(im, 5 * 1024, allow_downscale=True)
    assert len(data) <= 5 * 1024 and "downscaled" in label
    print("opted in:", len(data), "bytes,", label)
    print("OK: module 04")


if __name__ == "__main__":
    main()
