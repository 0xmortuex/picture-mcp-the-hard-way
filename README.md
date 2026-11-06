# picture-mcp: The Hard Way

Build an MCP server that does everyday image jobs for an AI agent: look at a photo, shrink
it to a size budget, strip the GPS before it is posted, and return a thumbnail so the agent
can see what it just made. Pillow and nothing else. Every line explained, every claim
checked by running real code on real images.

At the end you will have built a minimal version of
[picture-mcp](https://github.com/0xmortuex/picture-mcp) yourself, and you will know the
parts most image tutorials skip: **the arithmetic of resizing, why alpha breaks JPEG
conversion, how to search for a file size, what EXIF really contains and how to remove it
without re-encoding, and how to let an agent near a filesystem safely.**

## Who This Is For

- Developers who built a "hello world" MCP server and want one that touches real files
- Anyone who has been bitten by a sideways photo, a black-background JPEG or a leaked GPS tag
- People who want to know what happens between "make it 200 KB" and the bytes on disk

**Prerequisites:** Python 3.10+. `pip install -r requirements.txt` (that is `mcp` and
`Pillow`; no system packages, no ImageMagick, no ffmpeg).

## Modules

| # | Module | What You'll Build |
|---|--------|-------------------|
| 01 | [Pillow Basics](01-pillow-basics/) | Lazy open vs decode, modes, why the file name lies, and a describe function that detects truncation |
| 02 | [Resizing Math](02-resizing-math/) | fit, fill, exact and percent as pure arithmetic, never upscaling by accident, tested by table |
| 03 | [Formats and Alpha](03-formats-and-alpha/) | Flattening transparency onto a colour, keeping animations, palette and CMYK inputs, honest notes |
| 04 | [Size-Targeted Compression](04-size-targeted-compression/) | A binary search on JPEG quality that hits "under 200 KB", and what to do when it cannot |
| 05 | [EXIF and Privacy](05-exif-and-privacy/) | Writing and reading GPS, orientation, and a lossless JPEG stripper with a self-check |
| 06 | [Safe Batch and Paths](06-safe-batch-and-paths/) | A directory sandbox that survives `..` and symlinks, atomic writes, no overwrites, dry-run batch |
| 07 | [MCP Wrapper and Testing](07-mcp-wrapper-and-testing/) | A one-file MCP server with image previews, driven over real stdio by a test client |

Each module contains:
- **`README.md`**: the concepts and the design decisions
- **`main.py`**: a working, commented implementation that checks itself with `assert`
- **`break-it.md`**: challenges that break your own code, with hints

## How To Use This Course

**Option A: Build along.** Read the modules in order, run each `main.py`, then do the
break-it challenges.

**Option B: Reference.** Each `main.py` stands alone, with no imports between modules.

**Option C: Use the finished tool.** `uvx picture-mcp` is the full version of what
Module 07 assembles.

## Run It

```
pip install -r requirements.txt
python verify.py          # runs every module's main.py; each must exit 0
python verify.py 04 06    # just these
cd 07-mcp-wrapper-and-testing && python server.py --dir ~/Pictures   # the server itself
```

`verify.py` is what CI runs on Linux, macOS and Windows. The modules create their own test
images (gradients, transparent logos, animated GIFs, EXIF with GPS) in a temp directory, so
there are no fixtures to download.

## License

MIT
