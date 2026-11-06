"""A minimal picture-mcp: three tools, a sandbox, thumbnails. The whole server in one file.

Run it:  python server.py --dir ~/Pictures      (speaks MCP over stdio)
Test it: python main.py                         (launches this file as a subprocess)
"""

from __future__ import annotations

import argparse
import functools
import io
import os
import sys
import tempfile
from collections.abc import Callable
from typing import Any, TypeVar

from mcp.server.mcpserver import Image, MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from PIL import Image as PILImage
from PIL import ImageOps

PILImage.MAX_IMAGE_PIXELS = None
ALLOWED: list[str] = []
MAX_PIXELS = 100_000_000
GPS_IFD, ORIENTATION = 0x8825, 0x0112


class PictureError(Exception):
    """An expected failure. The message is written for the agent."""


def _inside(path: str, root: str) -> bool:
    try:
        return os.path.commonpath([path, root]) == root
    except ValueError:  # different drives on Windows
        return False


def resolve(path: str) -> str:
    """Collapse '..' and follow symlinks first, THEN check against the allowed folders."""
    real = os.path.realpath(os.path.expanduser(path))
    if ALLOWED and not any(_inside(os.path.normcase(real), r) for r in ALLOWED):
        raise PictureError(f"{path!r} is outside the allowed directories ({', '.join(ALLOWED)})")
    return real


def load(path: str) -> tuple[str, PILImage.Image]:
    real = resolve(path)
    if not os.path.isfile(real):
        raise PictureError(f"file not found: {real}")
    try:
        im = PILImage.open(real)
    except PILImage.UnidentifiedImageError:
        raise PictureError(f"{os.path.basename(real)} is not an image") from None
    if im.width * im.height > MAX_PIXELS:
        raise PictureError(f"{im.width}x{im.height} is over the {MAX_PIXELS // 10**6} MP safety limit")
    try:
        im.load()
    except OSError as e:
        raise PictureError(f"{os.path.basename(real)} is corrupt or truncated ({e})") from None
    return real, im


def thumbnail(im: PILImage.Image, side: int = 256) -> Image:
    """An MCP image content block: the agent can LOOK at what it just made."""
    t = im.convert("RGB")
    t.thumbnail((side, side))
    buf = io.BytesIO()
    t.save(buf, format="JPEG", quality=70)
    return Image(data=buf.getvalue(), format="jpeg")


mcp = MCPServer(
    "picture-mini",
    instructions="Inspect, resize and de-GPS images. Start with image_info. Never overwrites.",
)
F = TypeVar("F", bound=Callable[..., Any])


def tool(fn: F) -> F:
    """Register fn; turn PictureError into a ToolError so the agent sees the message.

    MCPServer replaces any other exception with a bare 'Error executing tool X', which
    tells the agent nothing. Wrap what you expect; let real bugs stay loud for you.
    """

    @functools.wraps(fn)
    def wrapper(*a: Any, **k: Any) -> Any:
        try:
            return fn(*a, **k)
        except PictureError as e:
            raise ToolError(str(e)) from e

    mcp.tool(structured_output=False)(wrapper)
    return fn


@tool
def image_info(path: str) -> str:
    """Describe an image: format, pixel size, mode, and whether it contains a GPS location.
    Call this first for any image; it also tells you if the file is corrupt."""
    real, im = load(path)
    gps = im.getexif().get_ifd(GPS_IFD)
    return (
        f"{real}\n{im.format} {im.width}x{im.height} {im.mode}, {os.path.getsize(real)} bytes\n"
        f"GPS: {'YES (use strip_gps before sharing)' if gps else 'none'}"
    )


@tool
def resize(path: str, width: int, overwrite: bool = False, preview: bool = False) -> list[str | Image]:
    """Resize to `width` pixels wide, keeping the aspect ratio, never enlarging.
    Writes photo.resized.jpg next to the input; refuses to overwrite unless overwrite=true.
    preview=true also returns a thumbnail of the result."""
    real, im = load(path)
    if width < 1:
        raise PictureError("width must be at least 1")
    im = ImageOps.exif_transpose(im)
    if width < im.width:
        im = im.resize((width, max(1, round(im.height * width / im.width))))
    root, ext = os.path.splitext(real)
    out = resolve(f"{root}.resized{ext}")
    if os.path.exists(out) and not overwrite:
        raise PictureError(f"{out} already exists. Pass overwrite=true or delete it.")
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(out), suffix=".tmp")
    os.close(fd)
    try:
        im.save(tmp, format="JPEG" if ext.lower() in (".jpg", ".jpeg") else None)
        os.replace(tmp, out)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    result: list[str | Image] = [f"Wrote {out}: {im.width}x{im.height}"]
    if preview:
        result.append(thumbnail(im))
    return result


@tool
def strip_gps(path: str) -> str:
    """Write a copy of the photo with ALL EXIF removed (GPS, camera, dates) as
    photo.stripped.jpg, rotating the pixels upright first. Verifies the copy is clean."""
    real, im = load(path)
    upright = ImageOps.exif_transpose(im).convert("RGB")
    root, _ = os.path.splitext(real)
    out = resolve(f"{root}.stripped.jpg")
    if os.path.exists(out):
        raise PictureError(f"{out} already exists. Delete it or move it first.")
    upright.save(out, format="JPEG", quality=95)  # no exif= argument: nothing is carried over
    with PILImage.open(out) as check:
        if check.getexif().get_ifd(GPS_IFD) or len(check.getexif()):
            os.unlink(out)
            raise PictureError("internal check failed: metadata survived; output deleted")
    return f"Wrote {out}. Verified: no GPS and no EXIF in the output."


def main() -> None:
    global ALLOWED
    p = argparse.ArgumentParser()
    p.add_argument("--dir", action="append", default=[])
    args = p.parse_args()
    ALLOWED = [os.path.normcase(os.path.realpath(d)) for d in args.dir]
    if ALLOWED:
        print("restricted to", ALLOWED, file=sys.stderr)  # stderr is safe; stdout is the protocol
    mcp.run()


if __name__ == "__main__":
    main()
