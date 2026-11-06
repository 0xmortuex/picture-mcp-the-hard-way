"""Module 06: Safe batch and paths - sandbox, no overwrites, atomic writes, dry runs.

Run: python main.py
"""

from __future__ import annotations

import contextlib
import glob
import os
import tempfile
from collections.abc import Iterator

from PIL import Image

Image.MAX_IMAGE_PIXELS = None  # we enforce our own, explicit limit below
ALLOWED: list[str] = []  # empty = unrestricted; otherwise real, case-normalised directories
MAX_PIXELS = 100_000_000


class PictureError(Exception):
    """Expected failure: its message is written for the agent."""


# ---------------------------------------------------------------- the sandbox


def resolve(path: str) -> str:
    """realpath() collapses '..' and follows symlinks - even a symlink as the last part.

    Checking the *resolved* path is the whole trick. Checking the string you were given
    is how '../' and symlinks walk out of a sandbox.
    """
    real = os.path.realpath(os.path.expanduser(path))
    if ALLOWED:
        norm = os.path.normcase(real)
        if not any(_inside(norm, root) for root in ALLOWED):
            raise PictureError(f"{path!r} is outside the allowed directories ({', '.join(ALLOWED)})")
    return real


def _inside(path: str, root: str) -> bool:
    # NOT path.startswith(root): "/data/ok-evil" starts with "/data/ok".
    try:
        return os.path.commonpath([path, root]) == root
    except ValueError:  # different drives on Windows
        return False


# ------------------------------------------------------------- safe writing


def output_name(src: str, tag: str) -> str:
    root, ext = os.path.splitext(src)
    return f"{root}.{tag}{ext}"  # photo.jpg -> photo.resized.jpg


def check_output(path: str, overwrite: bool) -> str:
    real = resolve(path)
    if os.path.exists(real) and not overwrite:
        raise PictureError(f"{real} already exists. Pass overwrite=true or choose another output.")
    return real


@contextlib.contextmanager
def atomic_target(final: str) -> Iterator[str]:
    """Write to a temp file in the SAME directory, then os.replace() it into place.

    Same directory matters: rename is only atomic within one filesystem. If anything
    raises, the temp file is deleted and the destination is untouched.
    """
    fd, tmp = tempfile.mkstemp(prefix=".pic-", suffix=".tmp", dir=os.path.dirname(final))
    os.close(fd)
    try:
        yield tmp
        os.replace(tmp, final)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(tmp)
        raise


def open_checked(path: str, allow_huge: bool = False) -> Image.Image:
    """Refuse decompression bombs BEFORE decoding: the header already says how big it is."""
    real = resolve(path)
    im = Image.open(real)
    pixels = im.width * im.height * getattr(im, "n_frames", 1)
    if pixels > MAX_PIXELS and not allow_huge:
        raise PictureError(
            f"{os.path.basename(real)} is {im.width}x{im.height} = {pixels / 1e6:.0f} MP, over the "
            f"{MAX_PIXELS / 1e6:.0f} MP limit. If you trust it, pass allow_huge=true."
        )
    im.load()
    return im


def resize_width(src: str, width: int, output: str | None = None, overwrite: bool = False) -> str:
    im = open_checked(src)
    out = check_output(output or output_name(resolve(src), "resized"), overwrite)
    height = max(1, round(im.height * width / im.width))
    with atomic_target(out) as tmp:
        im.resize((width, height), Image.Resampling.LANCZOS).save(tmp, format=im.format)
    return out


# ------------------------------------------------------------------- batch


def batch_resize(pattern: str, width: int, dry_run: bool = True) -> str:
    """Dry run by default: an agent that can touch 500 files should have to ask twice."""
    files = [f for f in sorted(glob.glob(pattern, recursive=True)) if os.path.isfile(f)]
    rows = []
    for f in files:
        try:
            real = resolve(f)  # a symlink in the folder may point outside: refuse that file only
        except PictureError as e:
            rows.append((os.path.basename(f), "REFUSED", str(e)))
            continue
        if ".resized." in os.path.basename(real):
            continue  # our own earlier output: do not resize it again
        out = output_name(real, "resized")
        if dry_run:
            state = "would FAIL (exists)" if os.path.exists(out) else "would write"
            rows.append((os.path.basename(real), state, os.path.basename(out)))
            continue
        try:
            resize_width(real, width)
            rows.append((os.path.basename(real), "ok", os.path.basename(out)))
        except (PictureError, OSError) as e:  # one bad file must not stop the other 499
            rows.append((os.path.basename(real), "FAILED", str(e).splitlines()[0]))
    head = "DRY RUN (nothing written)" if dry_run else "DONE"
    return head + "\n" + "\n".join(f"  {a:<20} {b:<20} {c}" for a, b, c in rows)


def main() -> None:
    global ALLOWED, MAX_PIXELS
    root = os.path.realpath(tempfile.mkdtemp(prefix="pic06-"))
    ok_dir = os.path.join(root, "ok")
    os.mkdir(ok_dir)
    ALLOWED = [os.path.normcase(ok_dir)]
    for i in range(3):
        Image.new("RGB", (400, 300), (i * 80, 40, 40)).save(os.path.join(ok_dir, f"p{i}.jpg"))
    open(os.path.join(ok_dir, "bad.jpg"), "wb").write(b"garbage")
    Image.new("RGB", (10, 10)).save(os.path.join(root, "secret.png"))

    # 1. The sandbox: traversal, outside paths, and the prefix trap.
    for evil in (os.path.join(root, "secret.png"), os.path.join(ok_dir, "..", "secret.png")):
        try:
            resolve(evil)
        except PictureError as e:
            assert "outside the allowed" in str(e)
        else:
            raise AssertionError(evil)
    sibling = ok_dir + "-evil"
    os.mkdir(sibling)
    try:
        resolve(os.path.join(sibling, "x.png"))
    except PictureError:
        print("prefix trap blocked:", os.path.basename(sibling))
    else:
        raise AssertionError("startswith() style check would have allowed this")

    # 2. Symlinks (needs permission on Windows; skip honestly if unavailable).
    link = os.path.join(ok_dir, "link.png")
    try:
        os.symlink(os.path.join(root, "secret.png"), link)
    except (OSError, NotImplementedError):
        print("symlink check skipped: no permission to create symlinks here")
    else:
        try:
            resolve(link)
        except PictureError:
            print("symlink escape blocked")
        else:
            raise AssertionError("symlink escaped the sandbox")

    # 3. Never overwrite; the original survives; outputs are named next to the input.
    first = resize_width(os.path.join(ok_dir, "p0.jpg"), 100)
    assert first.endswith("p0.resized.jpg") and Image.open(first).size == (100, 75)
    stamp = os.path.getmtime(first)
    try:
        resize_width(os.path.join(ok_dir, "p0.jpg"), 50)
    except PictureError as e:
        assert "overwrite=true" in str(e)
    else:
        raise AssertionError("must not overwrite")
    assert os.path.getmtime(first) == stamp and Image.open(first).width == 100
    resize_width(os.path.join(ok_dir, "p0.jpg"), 50, overwrite=True)
    assert Image.open(first).width == 50

    # 4. Atomic: a crash mid-write leaves the destination alone and no temp litter.
    before = sorted(os.listdir(ok_dir))
    try:
        with atomic_target(first) as tmp:
            open(tmp, "wb").write(b"half a file")
            raise RuntimeError("power cut")
    except RuntimeError:
        pass
    assert sorted(os.listdir(ok_dir)) == before and Image.open(first).width == 50
    print("atomic write: destination untouched, no temp files")

    # 5. Decompression bomb: a 3 MP PNG is a few KB on disk. Refuse by header, allow explicitly.
    big = os.path.join(ok_dir, "big.png")
    Image.new("RGB", (2000, 1500), (9, 9, 9)).save(big)
    MAX_PIXELS = 1_000_000
    try:
        resize_width(big, 100)
    except PictureError as e:
        assert "allow_huge=true" in str(e)
        print("bomb guard:", e)
    else:
        raise AssertionError("expected refusal")
    MAX_PIXELS = 100_000_000
    os.unlink(big)

    # 6. Batch: dry run lists the plan and writes nothing; the real run reports per file.
    pattern = os.path.join(ok_dir, "*.jpg")
    listing = os.listdir(ok_dir)
    plan = batch_resize(pattern, 100)
    print(plan)
    assert sorted(os.listdir(ok_dir)) == sorted(listing), "dry run must not write"
    assert "would write" in plan and "exists" in plan  # p0.resized.jpg already exists
    result = batch_resize(pattern, 100, dry_run=False)
    print(result)
    assert "FAILED" in result and "bad.jpg" in result  # the bad file is reported, not fatal
    assert Image.open(os.path.join(ok_dir, "p1.resized.jpg")).size == (100, 75)
    assert not any(".resized.resized" in f for f in os.listdir(ok_dir))
    print("OK: module 06")


if __name__ == "__main__":
    main()
