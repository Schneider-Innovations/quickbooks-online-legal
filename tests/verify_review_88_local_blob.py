"""Reconstruct the exact Release 88 local Review workflow admitted by the gate.

review-approved-pin-local.yml admits Git blob ca44e6ce for this repository's
codex-cli-review-receipt.yml. That blob is the snd-quality-gate c1b3428
reusable workflow rendered as this repository's local mirror
(review-release.py prepare-callers --spec review-2026-09-24.88.json). The
complete change from the protected-base mirror is in
tests/review-88-local-mirror.patch; applying it must yield the admitted blob.
"""

import hashlib
import pathlib
import re
import subprocess


PATH = ".github/workflows/codex-cli-review-receipt.yml"
BASE_BLOB = "b6bff6759ba60f83dfbd3542874b0e98b35ae5d7"
EXPECTED_BLOB = "ca44e6ce86aed933f34e6f30865c1e81d6399053"
PATCH = pathlib.Path(__file__).with_name("review-88-local-mirror.patch")


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
    print(f"verified complete Release 88 local Review workflow Git blob: {actual}")


if __name__ == "__main__":
    main()
