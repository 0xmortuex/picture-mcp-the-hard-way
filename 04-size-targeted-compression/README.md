# Module 04: Size-Targeted Compression

## The Concept

Nobody wants "quality 73". They want "under 200 KB for the upload form". JPEG and WebP take a
quality number, not a size, so a tool has to **search**: find the highest quality whose file
still fits. This module builds that search, then deals with the harder question: what to do
when no quality fits.

## Measure the Curve First

`main.py` encodes the same noisy 1200x800 image at five qualities:

```
quality -> bytes: {30: 155279, 50: 208098, 70: 271257, 85: 373445, 95: 585808}
```

Size grows with quality, steeply at the top (95 costs 57% more than 85). That monotonic
shape is what lets us binary search. The numbers also hold a warning: the *floor* at quality
30 is 155 KB. No quality setting gets this image to 100 KB.

## The Search

```
invariant: quality `a` fits the target, quality `b` does not
while b - a > 1:
    mid = (a + b) // 2
    encode at mid; if it fits: a = mid else b = mid
```

About six encodes instead of sixty-five. Three details matter:

- **Encode in memory** (`io.BytesIO`), not to disk, inside the loop. It is faster and leaves
  no litter if the search is abandoned.
- **Try the top first.** If quality 95 already fits, return it. Do not "improve" a file
  that is under budget by degrading it.
- **Check the floor second.** If quality 30 does not fit, the search cannot succeed; say so
  immediately instead of searching a range with no answer.

The result is measured on disk and compared with the target: `size <= target`, and
`size > 0.7 * target` so a lazy search that always returned quality 30 would fail the
test. The runs land within 1% of the budget (`299.7 KB` for 300 KB).

## When It Cannot Fit

Three honest options when even the floor is too big:

1. Raise the target.
2. Lower the minimum quality (uglier).
3. Shrink the pixels.

Option 3 changes the *dimensions*, which the user did not ask for. So the default is an
**error that lists all three**, and shrinking is opt-in (`allow_downscale=True`). When it is
on, bytes scale roughly with pixel count, so the loop estimates each side's scale factor as
`sqrt(target / size) * 0.95`, retries, and reports `downscaled to 180x120` in the result.

> A tool that silently returns a smaller picture than you asked for has made your decision
> for you. A tool that fails with the three options has handed the decision back.

## PNG Is Different

PNG is lossless: there is no quality to search. You can re-optimise (`optimize=True`) which
never changes pixels, or reduce the palette (`quantize(256)`, 128, 64...) which does. The
full picture-mcp offers `lossy_png=true` for the latter and says so when it is needed. The
exercise in the break-it file makes you see why.

## Run It

```
python main.py
```

## What To Notice

- `compress_to` never touches the disk; the test writes the bytes and measures the *file*.
  Measuring the thing the user will actually receive avoids "my accounting said 199 KB".
- The tolerance check (`> 0.7 * target`) guards against a bug class where a function is
  "correct" (under the limit) and useless (far under it).

→ [Next: Module 05](../05-exif-and-privacy/README.md)
