"""Module 05: EXIF and privacy - find the GPS, remove it losslessly, prove it is gone.

Run: python main.py
"""

from __future__ import annotations

import io
import os
import tempfile

from PIL import Image, ImageOps

GPS_IFD, ORIENTATION = 0x8825, 0x0112


def make_photo(path: str, orientation: int | None = None) -> None:
    """A JPEG with a camera make, a date and a GPS fix, written with Pillow's Exif API."""
    red = Image.linear_gradient("L").rotate(90).resize((200, 100))
    im = Image.merge("RGB", (red, Image.new("L", (200, 100), 60), Image.new("L", (200, 100), 90)))
    ex = Image.Exif()
    ex[0x010F] = "Acme Cameras"  # Make
    ex[0x0132] = "2026:01:02 03:04:05"  # DateTime
    if orientation:
        ex[ORIENTATION] = orientation
    gps = ex.get_ifd(GPS_IFD)  # a dict you fill in; tags 1..4 are lat ref, lat, lon ref, lon
    gps[1], gps[2], gps[3], gps[4] = "N", (41.0, 1.0, 30.0), "E", (29.0, 0.0, 0.0)
    ex[GPS_IFD] = gps
    im.save(path, exif=ex, quality=92, comment=b"shot by Bob")


def gps_of(raw: bytes) -> tuple[float, float] | None:
    with Image.open(io.BytesIO(raw)) as im:
        gps = im.getexif().get_ifd(GPS_IFD)
    if not gps:
        return None
    sign = lambda ref: -1 if ref in ("S", "W") else 1  # noqa: E731
    lat = sum(float(v) / d for v, d in zip(gps[2], (1, 60, 3600))) * sign(gps[1])
    lon = sum(float(v) / d for v, d in zip(gps[4], (1, 60, 3600))) * sign(gps[3])
    return lat, lon


def strip_jpeg(data: bytes, keep_orientation: int | None = None) -> tuple[bytes, list[str]]:
    """Lossless metadata removal: copy the JPEG segment by segment, dropping private ones.

    A JPEG is a list of segments `FF xx LL LL payload` until the start-of-scan marker
    (FF DA); after that comes entropy-coded pixel data up to the end marker (FF D9).
    We never decode the pixels, so they cannot change.
    """
    assert data[:2] == b"\xff\xd8", "not a JPEG"
    kept: list[bytes] = []
    dropped: list[str] = []
    i = 2
    while True:
        assert data[i] == 0xFF, "corrupt segment header"
        marker = data[i + 1]
        length = int.from_bytes(data[i + 2 : i + 4], "big")
        seg_end = i + 2 + length
        if marker == 0xDA:  # scan: find the end marker. 'FF 00' and 'FF D0-D7' are not markers.
            j = seg_end
            while True:
                k = data.index(b"\xff", j)
                nxt = data[k + 1]
                if nxt == 0 or 0xD0 <= nxt <= 0xD7 or nxt == 0xFF:
                    j = k + 2 if nxt != 0xFF else k + 1
                elif nxt == 0xD9:
                    end = k + 2
                    break
                else:  # another table/scan header (progressive JPEG)
                    j = k + 2 + int.from_bytes(data[k + 2 : k + 4], "big")
            kept.append(data[i:end])
            trailing = len(data) - end
            if trailing:
                dropped.append(f"{trailing} bytes after the image")
            break
        payload = data[i + 4 : seg_end]
        if marker == 0xE0 or marker == 0xEE:  # JFIF header; Adobe (needed to decode CMYK)
            kept.append(data[i:seg_end])
        elif marker == 0xE2 and payload.startswith(b"ICC_PROFILE\x00"):  # colors: keep
            kept.append(data[i:seg_end])
        elif 0xE0 <= marker <= 0xEF or marker == 0xFE:  # EXIF, XMP, IPTC, comment, ...
            dropped.append("comment" if marker == 0xFE else f"APP{marker - 0xE0}")
        else:  # quantization/huffman tables, frame header: required to decode
            kept.append(data[i:seg_end])
        i = seg_end
    if keep_orientation and keep_orientation != 1:
        ex = Image.Exif()
        ex[ORIENTATION] = keep_orientation
        body = ex.tobytes()
        body = body if body.startswith(b"Exif\x00\x00") else b"Exif\x00\x00" + body
        kept.insert(1 if kept[0][1] == 0xE0 else 0, b"\xff\xe1" + (len(body) + 2).to_bytes(2, "big") + body)
    return b"\xff\xd8" + b"".join(kept), dropped


def main() -> None:
    work = tempfile.mkdtemp(prefix="pic05-")
    photo = os.path.join(work, "trip.jpg")
    make_photo(photo, orientation=6)
    raw = open(photo, "rb").read() + b"HIDDEN-TRAILER"  # plus junk some phones append
    assert gps_of(raw) == (41.025, 29.0), gps_of(raw)
    print("found GPS:", gps_of(raw))

    # 1. Orientation: 6 means "rotate 90 clockwise to display". Stored 200x100, shown 100x200.
    with Image.open(io.BytesIO(raw)) as im:
        assert im.size == (200, 100) and im.getexif()[ORIENTATION] == 6
        upright = ImageOps.exif_transpose(im)
        assert upright.size == (100, 200) and ORIENTATION not in upright.getexif()
    print("exif_transpose: stored 200x100 -> displayed 100x200")

    # 2. Strip losslessly, keeping only the Orientation tag so the photo still shows upright.
    clean, dropped = strip_jpeg(raw, keep_orientation=6)
    print("dropped:", dropped)
    assert gps_of(clean) is None
    with Image.open(io.BytesIO(clean)) as a, Image.open(io.BytesIO(raw)) as b:
        assert dict(a.getexif()) == {ORIENTATION: 6}, dict(a.getexif())
        assert a.tobytes() == b.tobytes(), "pixels must be byte-identical (lossless)"
    for needle in (b"Acme", b"shot by Bob", b"HIDDEN-TRAILER", b"2026:01:02"):
        assert needle not in clean, needle
    assert len(clean) < len(raw)

    # 3. Verify the way a skeptic would: re-open the OUTPUT and look for anything left.
    with Image.open(io.BytesIO(clean)) as im:
        leftover = {k for k in im.getexif() if k != ORIENTATION}
        assert not leftover and not im.getexif().get_ifd(GPS_IFD)
    print("verified: no GPS, no EXIF but Orientation, pixels identical")

    # 4. The lossy alternative: bake the rotation in and re-encode with Pillow.
    with Image.open(io.BytesIO(raw)) as im:
        baked = io.BytesIO()
        ImageOps.exif_transpose(im).convert("RGB").save(baked, format="JPEG", quality=95)
    with Image.open(io.BytesIO(baked.getvalue())) as im:
        assert im.size == (100, 200) and not dict(im.getexif())
    print("re-encode path also clean (but lossy)")
    print("OK: module 05")


if __name__ == "__main__":
    main()
