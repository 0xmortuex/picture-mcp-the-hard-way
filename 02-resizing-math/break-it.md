# Break It: Resizing Math

## Challenge 1: Truncate Instead of Assigning

In the `fit` branch, compute `scale = min(width / w, height / h)` and set
`tw = int(w * scale)`. Then loop `w` over 100..5000 and count how often `tw != width` when
the width is the limiting side.

**Hint:** `int(289 * (800 / 289))` is 799: floating point lands a hair under the integer and
`int` truncates. (`round` hides it here, but still hands you a float-derived answer to a
question that has an exact one.) When one side is the limit, assign it directly and derive
only the other.

## Challenge 2: The Wrong Ratio

Swap `min` logic in `fit` so it uses the larger ratio. Which table cases fail, and what would
the image look like in real life?

**Hint:** The larger ratio makes the result overflow the box: that is `fill`'s behaviour
without the crop. Fit and fill are the same arithmetic with `min` versus `max`.

## Challenge 3: Stretch Instead of Crop

Make `fill` simply return `(width, height)` with no crop box. Does the table still pass?
Does the real-image check at the end still pass?

**Hint:** The table cannot tell, because the sizes are right. The pixel assertion catches
it: a squashed copy of the whole gradient has a much darker left edge (near 0) than a
centred crop. This is why tests measure content, not only dimensions.

## Challenge 4: A Pixel-Tall Image

Call `plan_resize(1000, 2, width=10)` and `plan_resize(2, 1000, height=10)`. Then try
`width=1` on a 1000x2 image. What goes wrong if you remove the `max(1, ...)`?

**Hint:** `round(2 * 10 / 1000)` is `0`, and Pillow refuses a zero-pixel dimension.
Extreme aspect ratios (banners, scans) hit this in real life.

→ [Next: Module 03](../03-formats-and-alpha/README.md)
