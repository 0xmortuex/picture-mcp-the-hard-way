# Module 06: Safe Batch and Paths

## The Concept

The moment an agent can name a file path, you have a security problem: it might be tricked
(by a prompt in a web page, a filename in a folder) into reading or overwriting something it
should not. This module builds the guard rails: a directory sandbox, a no-overwrite rule,
atomic writes, a decompression-bomb check and a batch mode that asks before it acts.

## The Sandbox: Check the Resolved Path

```python
real = os.path.realpath(os.path.expanduser(path))
```

`realpath` does two things: it collapses `..`, and it follows symlinks, including a symlink
as the *last* component. Only then do you compare against the allowed directories. Checking
the string you were given is how `ok/../secret.png` and `ok/link.png -> /etc/passwd` walk
out.

The comparison has its own trap:

```python
path.startswith(root)                       # WRONG
os.path.commonpath([path, root]) == root    # right
```

With `root = /data/ok`, the path `/data/ok-evil/x.png` starts with it. `main.py` creates that
sibling directory and checks it is refused. On Windows, `commonpath` raises `ValueError` for
paths on different drives, so that counts as "outside". Use `os.path.normcase` on both sides
so `C:\Photos` and `c:\photos` are the same place.

## Never Overwrite

Default behaviour: outputs are named next to the input (`photo.jpg` becomes
`photo.resized.jpg`) and if that file exists, the call fails with a message containing the
fix: `Pass overwrite=true or choose another output`. The test makes sure a refused call left
the earlier output's modification time and contents untouched. An agent that retries blindly
cannot destroy work.

## Atomic Writes

Writing straight to the destination means a crash (or an encoder error) leaves a half-written
file, possibly *replacing a good one*. The pattern:

1. Create a temp file in the **same directory** (rename is only atomic within one filesystem).
2. Write to it.
3. `os.replace(tmp, final)`: one atomic step.
4. On any exception, delete the temp file and re-raise.

`main.py` simulates a power cut inside the `with` block and asserts the directory listing is
unchanged and the destination still decodes.

## Decompression Bombs

A 20000x20000 solid-colour PNG is a few hundred KB on disk and a gigabyte in memory. Pillow
has a built-in guard, but it only *warns* between one and two times its limit, which is not a
guard. So we turn it off and apply our own rule *before decoding*: the header already says
the size, so compare `width * height * frames` with a limit (100 megapixels here) and raise
with a message that names the size and the explicit override (`allow_huge=true`). The test
lowers the limit and uses a real 3-megapixel file.

## Batch With a Dry Run

`batch_resize` defaults to `dry_run=True`: list what would be written, what would fail
because the output exists, and which files are refused. The agent has to call again with
`dry_run=False` to act. Properties worth copying:

- **One bad file does not stop the run.** Each file is wrapped; failures become rows in the
  result table (`FAILED  bad.jpg  not an image`).
- **A symlink pointing outside the sandbox refuses that one file**, not the whole batch.
- **Skip your own outputs.** Re-running over `*.jpg` must not turn `p0.resized.jpg` into
  `p0.resized.resized.jpg`.
- The final message is a table, so the agent can quote exactly what happened.

## Run It

```
python main.py
```

On Windows, creating symlinks may need Developer Mode or admin rights. If it is not
available the script says `symlink check skipped` rather than pretending it passed.

## What To Notice

- Every rule has an assert that *attempts the forbidden thing*. A guard you have never seen
  fire is a guess.
- Errors are `PictureError` with a human message; anything else is a bug and stays loud.
  Module 07 turns that distinction into what the agent sees.

→ [Next: Module 07](../07-mcp-wrapper-and-testing/README.md)
