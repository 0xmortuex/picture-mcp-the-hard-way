# Module 01: Pillow Basics

## The Concept

An image tool for an agent starts with one question: *what is this file?* Before any resize
or convert, the agent needs the format, the size, whether there is transparency, and whether
the file is even intact. This module builds that `describe()` function and, along the way,
the five facts about Pillow that every later module leans on.

```python
im = Image.open(path)   # reads the header only
im.size, im.mode, im.format
im.load()               # decodes every pixel
```

## Fact 1: Open Is Lazy, Load Is Not

`Image.open` reads just enough of the file to know the size and format. That makes it cheap
even for a 100-megapixel photo, and it is also why you can ask "how big is this?" without
paying for the decode. The cost is that **a truncated file opens without complaint**:

```python
with Image.open("cut.jpg") as im:
    im.size            # (200, 100): the header is intact
    im.load()          # OSError: image file is truncated
```

`describe()` therefore calls `load()` inside a `try`. If it fails, the description says
`WARNING corrupt/truncated` instead of letting a later tool crash with a stack trace.
Module 06 reuses the header-only property for a safety check.

## Fact 2: The Format Is in the Bytes

`im.format` comes from the file's magic bytes, not its extension. A PNG renamed to `.jpg`
opens as a PNG. Never decide what a file *is* from its name; decide what to *write* from
the name the user asks for.

## Fact 3: Modes Decide What You Can Do

`im.mode` is how pixels are stored: `RGB`, `RGBA` (with alpha), `L` (gray), `P` (palette,
at most 256 colours), `CMYK`, and a few exotic ones. Operations care:

- JPEG cannot store alpha: `RGBA.save("x.jpg")` raises `OSError: cannot write mode RGBA as
  JPEG` (Module 03 handles this properly).
- `resize` on a `P` image silently falls back to nearest-neighbour (blocky), because
  blending palette *indexes* would be meaningless. Convert to `RGB`/`RGBA` first.
- `convert("RGB")` is how you move between modes.

## Fact 4: Lossless and Lossy Are Measurable

`main.py` saves one gradient as PNG, JPEG and WebP and compares. For PNG the decoded bytes
are identical to the source (`tobytes()` equal); for JPEG they are not. "Lossless" is not a
claim to trust, it is an `assert` you can write. You will write many of those.

## Fact 5: Pixels Are Plain Data

`im.getpixel((x, y))` returns a tuple. The gradient helper makes red grow left to right and
green top to bottom, so a test can check pixel values and know what *should* be there. Every
later module verifies results by measuring pixels, never by looking at them and hoping.

## Run It

```
python main.py
```

Expected tail:

```
RGBA -> JPEG: cannot write mode RGBA as JPEG
OK: module 01
```

## What To Notice

- `describe()` raises `ValueError` for "not an image" but *returns* a warning string for
  "corrupt". Why different? A non-image is a wrong request; a damaged image is a finding the
  agent should report. Module 07 turns both into messages the agent can act on.
- Nothing here writes next to the input. Module 06 adds the rules for where outputs go.

→ [Next: Module 02](../02-resizing-math/README.md)
