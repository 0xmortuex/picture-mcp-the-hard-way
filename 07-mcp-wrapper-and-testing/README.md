# Module 07: MCP Wrapper and Testing

## The Concept

The previous modules are ordinary Python functions. An MCP server is a thin layer that
exposes them to an agent. "Thin" is the point: the logic stays testable without MCP, and the
wrapper's job is **names, descriptions, error translation and the shape of the reply**.

`server.py` in this module is the whole thing in one file: three tools (`image_info`,
`resize`, `strip_gps`), the sandbox from Module 06, and thumbnails.

## A Tool Is a Function Plus Its Docstring

```python
@tool
def resize(path: str, width: int, overwrite: bool = False, preview: bool = False): ...
```

The SDK builds the JSON schema from the type hints and uses the docstring as the description.
The agent reads the description as prose to decide *when* to call the tool and *what the
arguments mean*. `main.py` asserts every description is longer than 60 characters; a
one-word docstring fails the check. State the output location, the overwrite behaviour and
what `preview` returns.

## Errors Are the Agent's Only Feedback

In `mcp>=2`, if a tool raises an ordinary exception the client sees only a generic
`Error executing tool resize`. The message you carefully wrote never arrives. Only a
`ToolError` carries its text through. So the decorator catches *expected* failures
(`PictureError`: bad path, exists, not an image) and re-raises them as `ToolError`:

```python
except PictureError as e:
    raise ToolError(str(e)) from e
```

Anything else is a real bug and stays hidden from the agent on purpose; you see it in the
server's logs. The distinction between "the user asked for something impossible" and "my code
is broken" is the design.

## Letting the Agent See: Image Content

A tool may return a list mixing text and images:

```python
return [f"Wrote {out}: {w}x{h}", Image(data=jpeg_bytes, format="jpeg")]
```

The client receives a text block and an `image` content block with base64 data. A vision
model can *look* at the thumbnail of what it just produced and notice that the crop cut off
a head. The thumbnail is small (256 px, quality 70), so it costs little context. It is
opt-in (`preview=true`) because most calls do not need pixels.

Register such a tool with `structured_output=False`; an image object is not part of a JSON
schema.

## Don't Print to Stdout

In stdio mode, stdout *is* the protocol. A stray `print()` injects a non-JSON line into the
stream. Log to stderr. `server.py` announces its sandbox on stderr.

## Testing It For Real

`main.py` does not call the functions. It launches `server.py` as a subprocess over stdio,
exactly as Claude Desktop would, then speaks MCP:

1. `initialize`: the server name is `picture-mini`.
2. `tools/list`: exactly three tools, with real descriptions.
3. `image_info` on a photo with GPS: the text says `GPS: YES`.
4. `resize` with `preview=true`: the reply has **two** content blocks, `text` then `image`;
   the image decodes as a JPEG of the right shape. The photo is stored 800x600 with EXIF
   orientation 6, so the resized file must be 200x267, not 200x150. That checks the
   orientation handling *through the wire*.
5. A second `resize` fails with `is_error` and a message containing `overwrite=true`.
6. Paths outside `--dir` (including `ok/../outside.png`) are refused.
7. `strip_gps`: the output file is opened by the test and checked to hold no GPS and no EXIF,
   rather than trusting the tool's own "verified" line.

Why through the wire? Because the interesting bugs live in the seams: schema generation,
argument coercion, error translation, content encoding. A unit test of `resize()` cannot
fail on any of them.

## Run It

```
python main.py                              # the test
python server.py --dir ~/Pictures           # the server (give it to your MCP client)
```

Claude Code: `claude mcp add picture-mini -- python /full/path/to/server.py --dir ~/Pictures`

## Where To Go From Here

The finished [picture-mcp](https://github.com/0xmortuex/picture-mcp) adds the rest of the
tools (`convert`, `compress`, `crop`, `rotate_flip`, `contact_sheet`, `make_icons`,
`palette`, `batch`), animated-frame handling everywhere, the lossless JPEG stripper from
Module 05, size-targeted compression from Module 04 and a `--dir` flag with the sandbox from
Module 06. Its test suite follows this module's pattern: real images, measured outputs, and a
stdio session against the installed server.

→ Back to the [course index](../README.md)
