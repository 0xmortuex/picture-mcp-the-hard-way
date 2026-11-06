# Break It: Size-Targeted Compression

## Challenge 1: Linear Scan

Replace the binary search with a loop from `hi` down to `lo` that stops at the first quality
that fits. Time both on the 1200x800 image.

**Hint:** Same answer, many more encodes (up to 65 against 6). On a 20-megapixel photo each
encode takes a good fraction of a second; the difference is the gap between instant and
"is it hung?".

## Challenge 2: Search Without a Floor

Set `lo=1` in `best_quality`, then ask for 100 KB on the noisy image (it lands around quality 15). What does the
result look like (save it and open it)?

**Hint:** It "succeeds" at a quality where blocks are obvious. The default floor of 30 exists
so the tool says "cannot reach this target without ruining the picture" instead of handing
back a ruined picture. A floor is a promise about quality.

## Challenge 3: Optimise Away the Wrong Thing

Remove `optimize=True` from `encode`. Re-measure the curve. Then add `progressive=True`.

**Hint:** `optimize` makes Pillow compute better entropy tables: smaller files at identical
pixels, so it is free. Progressive JPEGs are often a bit smaller too, and render coarse to
fine on slow connections. Neither changes pixels, so they belong in every encode.

## Challenge 4: PNG and a Target

Save the noisy image as PNG and try to hit a third of its size with
`optimize=True` alone. Then try `im.quantize(64).save(...)`.

**Hint:** Lossless optimisation barely moves noisy content; the palette version is far
smaller but has visibly fewer colours. Because that is lossy, a tool should make you ask for
it. Which parameter name would make the cost obvious to an agent reading the schema?

## Challenge 5: Raise the Ceiling

Set `hi=100` and measure `encode(im, 95)` against `encode(im, 100)`.

**Hint:** On the noisy test image, 95 is 586 KB and 100 is 986 KB: 68% more bytes for
differences nobody can see. The search ceiling of 95 is a deliberate choice, the same kind of
choice as the floor in Challenge 2.

→ [Next: Module 05](../05-exif-and-privacy/README.md)
