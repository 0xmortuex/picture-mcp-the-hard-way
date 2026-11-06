# Module 03: Formats and Alpha

## The Concept

Converting formats looks like `im.save("out.webp")`. It stops being trivial the moment the
input has something the output cannot hold: transparency going to JPEG, an animation going
to a still format, a palette or CMYK image going anywhere. The rule for this module is
**do the sensible thing, and tell the user what you did**.

## Transparency Into JPEG

JPEG has no alpha channel. Two wrong answers are common:

1. Let Pillow raise `cannot write mode RGBA as JPEG`. Honest, useless to a user.
2. `im.convert("RGB")`: works, and gives you a **black** background, because the colour
   hidden under fully transparent pixels is usually `(0, 0, 0)`. `main.py` demonstrates this.

The right answer is to **composite onto a background colour**, which is what a browser would
show. Create a solid image in that colour and `Image.alpha_composite` the RGBA on top:

```python
base = Image.new("RGBA", rgba.size, (r, g, b, 255))
flat = Image.alpha_composite(base, rgba).convert("RGB")
```

The tool exposes the colour (`background="#ffffff"`, any name Pillow's `ImageColor` knows)
and reports `transparency flattened onto #00ff00`. The test checks both halves: the
transparent area became the requested green, and the opaque red stayed red.

## Animations

A GIF or WebP is a list of frames plus durations. `Image.n_frames`, `seek(i)` and
`info["duration"]` read them. Two details cost real debugging time:

- **WebP reports a frame's duration only after you `load()` it.** Read `info["duration"]`
  straight after `seek` and you get the default, so every converted animation silently runs
  at the wrong speed.
- Frames must share a mode to be re-saved together, so we convert each to RGBA.

Writing an animation back uses `save_all=True, append_images=frames[1:], duration=[...],
loop=0`. GIF, WebP and PNG (APNG) can animate; JPEG and BMP cannot. If the destination
cannot, take the first frame **and say so**. `main.py` asserts both paths: gif to webp keeps
5 frames at 120 ms each; gif to jpg returns the note `animation flattened to its first
frame`.

## Palette and CMYK Inputs

`P` (palette) and `CMYK` images need converting before most operations. `convert("RGB")`
handles `P`. For CMYK, Pillow's plain conversion is a rough approximation of the colours; a
production tool uses the embedded ICC profile when there is one. The chapter checks that a
pure CMYK red comes out red (high R, low G and B), and the full picture-mcp reports "CMYK
converted to RGB" in its notes.

## Return Notes, Not Silence

`convert()` returns a list of strings describing every lossy decision. That list becomes
part of the tool's reply in Module 07. An agent that is told "transparency flattened onto
white" can decide whether that was acceptable; an agent told nothing assumes success.

## Run It

```
python main.py
```

## What To Notice

- `load_frames` uses `convert("RGBA")` for every input. One internal representation means
  one code path; the format-specific work happens at the edges (load and save).
- The "naive" conversion is executed and asserted *wrong* before the right one is shown.
  When you build a fix, first prove the bug exists.

→ [Next: Module 04](../04-size-targeted-compression/README.md)
