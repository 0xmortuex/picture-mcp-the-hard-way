# Break It: EXIF and Privacy

## Challenge 1: Forget the Trailer

In `strip_jpeg`, replace `end = k + 2` handling so the function returns `data` up to the end
of the file rather than truncating at `FF D9`. Run `main.py`.

**Hint:** The `HIDDEN-TRAILER` assertion fails. Anything after the end-of-image marker is
invisible to viewers and perfectly readable to anyone who looks at the bytes.

## Challenge 2: Drop Everything

Pass `keep_orientation=None` for the photo with orientation 6, then open the result in an
image viewer (or check `Image.open(...).getexif()`).

**Hint:** It is clean, and it now displays sideways in anything that honoured the tag. That
is the trade-off the default resolves by keeping one tag, or by baking the rotation in.

## Challenge 3: A Naive Marker Scan

In the scan loop, treat every `FF` as a marker. Strip a progressive JPEG
(`im.save(..., progressive=True)`) and a photo with restart intervals.

**Hint:** `FF 00` (an escaped `FF` inside pixel data) and `FF D0..D7` (restart markers)
are not segment boundaries. A scanner that stops there truncates the image or stops early.

## Challenge 4: Keep the ICC Profile?

Delete the `ICC_PROFILE` branch from `strip_jpeg`, then convert a photo that carries a
colour profile (any phone photo, or `im.save(..., icc_profile=...)`).

**Hint:** Colours shift in profile-aware viewers (wide-gamut photos look washed out). The
profile describes colour, not the person; it is the one APP segment worth keeping.

## Challenge 5: Other Formats

PNG keeps text in `tEXt`/`iTXt` chunks and sometimes an `eXIf` chunk. Write a photo to PNG
with `pnginfo` and an Author, then see what `Image.open(...).save(...)` without any `pnginfo`
keeps.

**Hint:** Re-saving through Pillow drops the text chunks, and PNG is lossless, so the
simple route is also pixel-perfect for PNG. The JPEG-specific segment surgery only exists to
avoid *re-encoding a lossy format*.

→ [Next: Module 06](../06-safe-batch-and-paths/README.md)
