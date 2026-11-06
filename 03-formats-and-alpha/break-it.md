# Break It: Formats and Alpha

## Challenge 1: Convert Without Flattening

In `convert`, replace `flatten(f, background)` with `f.convert("RGB")` and rerun. Which
assertion fails and what colour is the logo's background?

**Hint:** The transparent half comes out black (or whatever sits under the alpha), not the
green you asked for. The bug is visible only in the pixels you did not draw on.

## Challenge 2: Read Durations Too Early

In `load_frames`, delete the `im.load()` line, then convert the GIF to WebP and back to GIF.
Print the durations after each step.

**Hint:** WebP exposes `duration` only for decoded frames, so you get the 100 ms default
instead of 120. The animation plays at the wrong speed and nothing raises an error.

## Challenge 3: A Semi-Transparent Edge

Create an RGBA image with a soft alpha ramp (`Image.linear_gradient("L")` as the alpha
channel over a solid red). Convert to JPEG once with `background="white"` and once with
`background="black"`. Compare the centre column.

**Hint:** Partially transparent pixels blend with whichever background you chose, so the
same source gives two different-looking JPEGs. This is why `background` is a parameter and
not a hidden constant.

## Challenge 4: Where Is the Warning?

Remove the `notes.append(...)` calls from `convert` and rerun the asserts that check the
notes. Then explain, in one sentence, why a tool that gets the pixels right but says
nothing is still worse than one that says what it did.

**Hint:** The caller (an agent) cannot see the pixels. Its only evidence about what
happened is your text.

→ [Next: Module 04](../04-size-targeted-compression/README.md)
