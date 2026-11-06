# Module 02: Resizing Math

## The Concept

"Make it 800 wide" sounds trivial until the request is "make it 800 by 800" for a 4:3 photo.
Does the result stretch, crop, or leave bars? A good tool names those choices instead of
guessing, and never enlarges a small image unless told to (upscaling adds bytes, not detail).

The trick is to keep the **arithmetic separate from the pixels**. `plan_resize()` takes
numbers and returns numbers: no Pillow, no files. That makes it testable with a table in a
millisecond, and it is the function you reason about when an agent says "the thumbnail came
out wrong".

## The Four Modes

| Request | Behaviour |
|---------|-----------|
| `width` only (or `height` only) | The other side follows the aspect ratio |
| `percent` | Both sides scaled; `> 100` is an error unless `allow_upscale` |
| `fit` with both | Largest size that fits *inside* the box. Compare `width / w` with `height / h` and take the smaller ratio |
| `exact` | Stretch to the box. The only mode that distorts |
| `fill` | *Cover* the box, then centre-crop the overflow (avatars, thumbnails) |

### fit: take the smaller ratio

A 4000x3000 photo into an 800x800 box: `800/4000 = 0.2` and `800/3000 = 0.267`. The smaller
ratio (0.2) is the one that does not overflow, so the result is 800x600. When the ratios say
the width is the limit, set `tw = width` exactly and *derive* `th`; do not multiply both
by a float and round, or you get 799 instead of 800.

### fill: crop first, then scale

To fill 400x400 from 4000x3000, first cut the largest centred region with the box's aspect
ratio (3000x3000 at `left=500`), then scale it to 400x400. Cropping first means you resize
fewer pixels and the result is exact. `plan_resize` returns the crop box and the final size
as a pair.

## Never Upscale by Accident

Every mode has a no-upscale branch. A 100x50 image asked for 400 wide stays 100x50 and says
so in `notes`. The alternative (silently making a blurry 400x200) is the kind of surprise
that costs an hour. It is an *explicit* switch: `allow_upscale=True`.

For `fill` with a small source there is a third outcome: crop to the target's aspect ratio
but do not scale up, so a 100x50 source asked for 400x400 gives 50x50 and a note.

## Errors That Tell You What To Do

`percent=150` raises `percent > 100 enlarges the image; pass allow_upscale=True`. Compare
with `ValueError("bad percent")`: the first message contains the fix. In Module 07 these
messages travel to the agent verbatim.

## The Filter

`Image.Resampling.LANCZOS` is the high-quality choice for shrinking. For RGBA images Pillow
premultiplies alpha internally during resizing, which avoids dark halos around transparent
edges. Nothing for you to do, but good to know it is happening.

## Run It

```
python main.py
```

`main.py` runs a table of 11 cases, then resizes a real gradient with `mode="fill"` and
*measures* the output: the left edge must be darker than the right (so it really is the
centre of the gradient, not a squashed copy of the whole thing), and both must lie in the
middle third of the ramp.

## What To Notice

- The test for `fill` checks pixel values, not just the output size. A function that
  stretched instead of cropping would also produce 50x50.
- `plan_resize` never raises for "too big a request" except `percent`. Think about why:
  asking for 800 wide on a 600-wide image is a reasonable request that deserves an answer
  plus a note, not an exception.

→ [Next: Module 03](../03-formats-and-alpha/README.md)
