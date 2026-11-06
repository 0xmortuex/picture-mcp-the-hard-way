"""Run every module's main.py and require exit code 0.

Each main.py checks its own results with assert, so a chapter whose code drifts out of
sync with what its README claims fails here. No QEMU, no external tools: Pillow and mcp.

Usage: python verify.py            # all modules
       python verify.py 04 06      # just these
"""

from __future__ import annotations

import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))


def main() -> int:
    wanted = sys.argv[1:]
    modules = sorted(
        d for d in os.listdir(ROOT)
        if os.path.isfile(os.path.join(ROOT, d, "main.py"))
        and (not wanted or any(d.startswith(w) for w in wanted))
    )
    if not modules:
        print("no modules matched")
        return 1
    failed = []
    for m in modules:
        start = time.monotonic()
        try:
            proc = subprocess.run(
                [sys.executable, "main.py"], capture_output=True, text=True, timeout=180,
                cwd=os.path.join(ROOT, m), encoding="utf-8", errors="replace",
            )
            ok, output = proc.returncode == 0, proc.stdout + proc.stderr
        except subprocess.TimeoutExpired:
            ok, output = False, "timed out after 180s"
        print(f"{'PASS' if ok else 'FAIL'}  {m}  ({time.monotonic() - start:.1f}s)")
        if not ok:
            failed.append(m)
            print("    " + output.strip().replace("\n", "\n    "))
    print(f"\n{len(modules) - len(failed)}/{len(modules)} modules verified")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
