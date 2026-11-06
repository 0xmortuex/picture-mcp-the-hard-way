"""Module 07: MCP wrapper and testing - drive the real server over real stdio.

Run: python main.py
This launches server.py as a subprocess, exactly like Claude Desktop would, and talks MCP to it.
"""

from __future__ import annotations

import asyncio
import base64
import io
import os
import sys
import tempfile

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
GPS_IFD = 0x8825


def make_photo(path: str) -> None:
    ex = Image.Exif()
    ex[0x010F] = "Acme Cameras"
    gps = ex.get_ifd(GPS_IFD)
    gps[1], gps[2], gps[3], gps[4] = "N", (41.0, 1.0, 30.0), "E", (29.0, 0.0, 0.0)
    ex[GPS_IFD] = gps
    ex[0x0112] = 6  # stored sideways
    Image.new("RGB", (800, 600), (200, 60, 60)).save(path, exif=ex)


async def run() -> None:
    root = os.path.realpath(tempfile.mkdtemp(prefix="pic07-"))
    ok = os.path.join(root, "ok")
    os.mkdir(ok)
    photo = os.path.join(ok, "trip.jpg")
    make_photo(photo)
    Image.new("RGB", (10, 10)).save(os.path.join(root, "outside.png"))

    params = StdioServerParameters(
        command=sys.executable, args=[os.path.join(HERE, "server.py"), "--dir", ok]
    )
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        init = await session.initialize()
        assert init.server_info.name == "picture-mini"

        # 1. The agent's view of the server: names and descriptions. This is all it has.
        tools = (await session.list_tools()).tools
        assert {t.name for t in tools} == {"image_info", "resize", "strip_gps"}
        for t in tools:
            assert t.description and len(t.description) > 60, f"{t.name}: description too thin"
        print("tools:", [t.name for t in tools])

        # 2. A real call against a real file.
        res = await session.call_tool("image_info", {"path": photo})
        assert not res.is_error and "GPS: YES" in res.content[0].text, res.content
        print(res.content[0].text)

        # 3. preview=true: text AND an image block the model can look at. Decode it for real.
        res = await session.call_tool("resize", {"path": photo, "width": 200, "preview": True})
        assert [c.type for c in res.content] == ["text", "image"], res.content
        thumb = Image.open(io.BytesIO(base64.b64decode(res.content[1].data)))
        assert res.content[1].mime_type == "image/jpeg"
        # orientation 6: stored 800x600, shown 600x800 -> 200 wide is 200x267; thumbnail max 256
        assert max(thumb.size) == 256 and thumb.width < thumb.height, thumb.size
        with Image.open(os.path.join(ok, "trip.resized.jpg")) as out:
            assert out.size == (200, 267)
        print("resize ->", res.content[0].text, "| thumbnail", thumb.size)

        # 4. Errors must reach the agent as readable text (is_error, not a crash).
        res = await session.call_tool("resize", {"path": photo, "width": 100})
        assert res.is_error and "overwrite=true" in res.content[0].text, res.content
        print("second resize ->", res.content[0].text)

        # 5. The sandbox holds over the wire, including '..'.
        for evil in (os.path.join(root, "outside.png"), os.path.join(ok, "..", "outside.png")):
            res = await session.call_tool("image_info", {"path": evil})
            assert res.is_error and "outside the allowed" in res.content[0].text, res.content
        print("sandbox: outside paths refused")

        # 6. The privacy tool, verified by us, not by the server's own claim.
        res = await session.call_tool("strip_gps", {"path": photo})
        assert not res.is_error, res.content
        with Image.open(os.path.join(ok, "trip.stripped.jpg")) as clean:
            assert not clean.getexif().get_ifd(GPS_IFD) and len(clean.getexif()) == 0
            assert clean.size == (600, 800)  # rotated upright into the pixels
        print(res.content[0].text)

    print("OK: module 07")


if __name__ == "__main__":
    asyncio.run(run())
