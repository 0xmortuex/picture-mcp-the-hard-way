# Break It: Pillow Basics

## Challenge 1: Trust the Extension

Change `describe()` to decide the format from `os.path.splitext(path)[1]` instead of
`im.format`. Run it on the `liar.jpg` the script creates. What does the agent now believe?

**Hint:** It says JPEG for a PNG. Then a tool that "re-saves as JPEG to keep the format"
would silently recompress a lossless file. Magic bytes decide what a file is.

## Challenge 2: Skip `load()`

Remove the `im.load()` call and run on `cut.jpg`. What does `describe()` print?

**Hint:** Perfectly healthy output. The damage only appears at decode time, which is why the
check lives in `describe()`. Where else would it surface if you skipped it, and who would
see the error?

## Challenge 3: A Huge File

Create `Image.new("RGB", (20000, 20000))` and save it as PNG (it is only a few hundred KB
on disk). Time `Image.open` and then `Image.open` + `load()`. Watch your memory use.

**Hint:** Open is instant; load allocates 20000 x 20000 x 3 = 1.2 GB. A tiny file can ask
for enormous memory, which is exactly why Module 06 inspects the header before decoding.

## Challenge 4: Palette Surprise

`Image.linear_gradient("L").convert("RGB").quantize(8)` gives a `P` image. Call `.resize`
with `LANCZOS` on it, then on its `convert("RGB")`. Compare the two results: the mode that comes back and `getcolors()` on each.

**Hint:** The palette version stays `P` with only 8 colours: Pillow quietly ignored
`LANCZOS` and used nearest-neighbour, because blending palette indexes is meaningless. The
RGB version has dozens of smooth in-between colours. Normalise the mode before you do
geometry; Module 03 does.

→ [Next: Module 02](../02-resizing-math/README.md)
