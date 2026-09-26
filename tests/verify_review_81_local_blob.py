"""Reconstruct the exact Release 81 local Review workflow admitted by the gate.

review-approved-pin-local.yml admits Git blob b8f028a9 for this repository's
codex-cli-review-receipt.yml. That blob is the snd-quality-gate 71676af
reusable workflow rendered as this repository's local mirror
(review-release.py prepare-callers --spec review-2026-09-24.81.json). The
complete change from the protected-base mirror is in
tests/review-81-local-mirror.patch; applying it must yield the admitted blob.
"""

import hashlib
import pathlib
import re
import subprocess


PATH = ".github/workflows/codex-cli-review-receipt.yml"
BASE_BLOB = "e15f7880fa78fdf2346d2c0d10a65c52b0d4089b"
EXPECTED_BLOB = "b8f028a9d1d9bbac02ab1403e121a9a481fa162b"
PATCH = pathlib.Path(__file__).with_name("review-81-local-mirror.patch")


def git_blob(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def apply_patch(base: bytes, patch: bytes) -> bytes:
    """Apply a unified diff with exact context; any mismatch fails."""
    old = base.split(b"\n")
    out, pos = [], 0
    lines = patch.replace(b"\r\n", b"\n").split(b"\n")
    i = next(n for n, line in enumerate(lines) if line.startswith(b"@@"))
    while i < len(lines) and lines[i].startswith(b"@@"):
        start = int(re.match(rb"@@ -(\d+)", lines[i]).group(1)) - 1
        assert start >= pos, "overlapping hunks"
        out += old[pos:start]
        pos = start
        i += 1
        while i < len(lines) and lines[i][:1] in (b" ", b"-", b"+"):
            tag, text = lines[i][:1], lines[i][1:]
            if tag in (b" ", b"-"):
                assert old[pos] == text, f"context mismatch at line {pos + 1}"
                pos += 1
            if tag in (b" ", b"+"):
                out.append(text)
            i += 1
    assert all(not line for line in lines[i:]), "unexpected trailing patch content"
    return b"\n".join(out + old[pos:])


def main() -> None:
    protected_base = subprocess.check_output(["git", "show", f"HEAD:{PATH}"])
    assert git_blob(protected_base) == BASE_BLOB, "protected-base workflow changed"
    actual = git_blob(apply_patch(protected_base, PATCH.read_bytes()))
    assert actual == EXPECTED_BLOB, f"candidate workflow blob mismatch: {actual}"
    print(f"verified complete Release 81 local Review workflow Git blob: {actual}")


if __name__ == "__main__":
    main()
