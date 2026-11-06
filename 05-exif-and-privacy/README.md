# Module 05: EXIF and Privacy

## The Concept

A phone photo carries a hidden document: the camera make and model, the exact time, the
software, sometimes a serial number, and often **where you were standing to a few metres**.
Post the file and you post the document. A privacy tool must (1) find what is there,
(2) remove it **without damaging the picture**, and (3) prove it is gone.

## Where EXIF Lives

A JPEG is a sequence of segments, each `FF xx LL LL payload`, followed by the compressed
pixels:

```
FF D8                       start of image
FF E0 ..  JFIF header       keep
FF E1 ..  "Exif\0\0" ...    EXIF: make, model, date, GPS...   <- drop
FF E1 ..  XMP packet        <- drop
FF ED ..  Photoshop/IPTC    <- drop
FF FE ..  comment           <- drop
FF DB / FF C4 / FF C0       quantization, Huffman tables, frame header   keep (needed)
FF DA ..  start of scan, then entropy-coded pixels
FF D9                       end of image   ... and anything after it is NOT part of the image
```

Pillow's Exif API reads and writes the tags. GPS is a sub-directory (IFD `0x8825`):
`exif.get_ifd(0x8825)` returns a dict, tags 1 to 4 being latitude reference, latitude as
degrees/minutes/seconds, longitude reference, longitude. `main.py` writes a photo with GPS
using nothing but this API, so the tests need no external files.

## Orientation

Cameras store pixels the way the sensor read them and add an Orientation tag (`0x0112`) that
says how to rotate for display. Value 6 means "rotate 90 degrees clockwise to display": a
photo stored as 200x100 is shown as 100x200. Viewers honour it; many tools do not, so
"resize this to 100 wide" gives different answers depending on who looks.

`ImageOps.exif_transpose(im)` bakes the rotation into the pixels and removes the tag. Every
geometry tool in picture-mcp calls it first, so sizes mean what a viewer shows.

## Removing Metadata Without Touching the Pixels

The easy way, `Image.open(...).save(...)` without `exif=`, drops metadata but **re-encodes**
the JPEG, which is lossy: a second round of compression artefacts for no reason.

`strip_jpeg()` instead copies segments: keep JFIF, the ICC colour profile and the tables the
decoder needs; drop EXIF, XMP, IPTC and comments; copy the pixel data byte for byte. Two
subtleties:

- **Finding the end of the pixels.** Inside entropy-coded data a literal `FF` byte is
  followed by `00`, and `FF D0` to `FF D7` are restart markers. Any other `FF xx` is a real
  marker; `FF D9` is the end. Progressive JPEGs have several scans, so a marker that is not
  `D9` is skipped by its length and the scan continues.
- **Trailing data.** Some files append things after `FF D9` (embedded previews, vendor
  blobs) that may hold their own copy of the GPS. The stripper truncates there and reports
  the byte count. The test appends `HIDDEN-TRAILER` and checks it is gone.

If the photo has an Orientation tag, dropping all EXIF would make it display sideways. So the
default keeps exactly one tag: a minimal EXIF segment containing only Orientation. The
alternative (`exif_transpose` and re-encode) is shown last in `main.py`, and it is lossy.

## Prove It

The end of `main.py` re-opens the **output**, not the function's own bookkeeping:

- no GPS directory,
- the only tag left is Orientation,
- `tobytes()` of the decoded image equals the original's (lossless),
- the raw bytes contain none of `Acme`, `shot by Bob`, `HIDDEN-TRAILER`, `2026:01:02`.

A privacy tool that says "removed" without checking has told you what it intended.

## Run It

```
python main.py
```

## What To Notice

- `gps_of` converts degrees/minutes/seconds to decimal. Showing the user *which* location
  was about to leak is more convincing than "GPS: yes".
- The stripper is about 50 lines and decodes nothing. Knowing a file format's container
  structure often beats reaching for a library.

→ [Next: Module 06](../06-safe-batch-and-paths/README.md)
