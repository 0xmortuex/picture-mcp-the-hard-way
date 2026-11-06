# Break It: MCP Wrapper and Testing

## Challenge 1: Print to Stdout

Add `print("loading", path)` at the top of `load()` in `server.py` and run `main.py`. Then
change it to `print(..., file=sys.stderr)`.

**Hint:** The first version writes a non-JSON line into the protocol stream. Depending on
the SDK version the client skips it, errors, or loses sync. Stderr is free for logs.

## Challenge 2: Raise a Plain Exception

In `resize`, replace one `raise PictureError(...)` with `raise ValueError(...)` and rerun the
overwrite check. Look at `res.content[0].text`.

**Hint:** The agent gets a generic "Error executing tool resize" and cannot tell the user
what to do. This is the whole reason the decorator exists. Which of your failures are
"expected", and which should stay loud?

## Challenge 3: A Docstring of One Word

Change the `resize` docstring to `"""Resize."""`. Which assertion fails? Now imagine you
are the model: given only that description, would you know that it will not overwrite, where
the output goes, or what `preview` returns?

**Hint:** The description is your whole interface. It must say when to use the tool, what
the arguments mean and what the result looks like.

## Challenge 4: Return the Full-Size Image

Make `thumbnail` return the full-resolution JPEG. What happens to the reply size for a
20-megapixel photo?

**Hint:** Megabytes of base64 land in the model's context for a quick look. The small
thumbnail is a deliberate trade: enough to see composition, cheap enough to use freely.

## Challenge 5: Remove the Sandbox Check From the Shared Helper

In `load()`, replace `real = resolve(path)` with `real = os.path.realpath(path)` and rerun
`main.py`.

**Hint:** The outside-path assertions fail for every tool at once. That is the point of
putting the check in the one helper all tools go through: a new tool that calls `load()` is
safe by default, and the one that opens files itself is the one that forgets.

→ Back to the [course index](../README.md)
