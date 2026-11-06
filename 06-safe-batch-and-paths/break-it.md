# Break It: Safe Batch and Paths

## Challenge 1: The startswith Check

Replace `_inside` with `return path.startswith(root)` and run `main.py`.

**Hint:** The `ok-evil` sibling is now accepted, and the script's assertion fails. Prefix
checks on strings are the classic path-sandbox bug.

## Challenge 2: Check Before Resolving

In `resolve`, run the allow-list check on `os.path.abspath(path)` instead of the
`realpath`. Run `main.py` on a machine where symlinks work.

**Hint:** `abspath` collapses `..` but does not follow links, so `ok/link.png` looks like it
is inside `ok` while pointing at the secret. The symlink assertion fails.

## Challenge 3: Write Directly

Change `resize_width` to save straight to `out` without `atomic_target`, and make the write
fail halfway: wrap it as `with open(out, "wb") as f: f.write(b"half"); raise RuntimeError`.
Run it on a file that already exists with `overwrite=True`, then look at the destination.

**Hint:** The good file has been replaced by four bytes of garbage. With the temp-file
pattern the old file survives byte for byte, which `main.py`'s power-cut simulation asserts.

## Challenge 4: Temp File in /tmp

In `atomic_target`, create the temp file with the default directory (remove `dir=`). On
Linux, `/tmp` is often a different filesystem from your photos.

**Hint:** `os.replace` across filesystems raises `OSError: Invalid cross-device link`, or
(with other APIs) falls back to a copy, which is not atomic. Keep the temp file next to the
destination.

## Challenge 5: Re-run Over Your Own Outputs

Delete the `.resized.` skip in `batch_resize`, run the real batch twice with
`overwrite=True`, and list the folder.

**Hint:** Now `p0.resized.jpg` is resized again into `p0.resized.resized.jpg`, and every
re-run grows the folder. A batch tool must recognise its own output names.

Then reflect on the default: `dry_run=True` makes the cheap, reversible step (listing) the
default and the effectful one an explicit second call. Defaults are policy.

→ [Next: Module 07](../07-mcp-wrapper-and-testing/README.md)
