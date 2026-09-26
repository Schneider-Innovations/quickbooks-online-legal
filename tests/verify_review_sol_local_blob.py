"""Reconstruct the exact Sol policy workflow admitted by the local gate.

The candidate keeps the protected-base workflow byte-for-byte except for one
policy digest. Git blob identity binds the whole resulting workflow, not just
the digest line shown in the pull request.
"""

import hashlib
import subprocess


PATH = ".github/workflows/codex-cli-review-receipt.yml"
BASE_BLOB = "93c522ac35b1820079b2e3016cb67be2c8fcf03d"
ANCHOR = (
    b"              '487b8e2d43db74160c50b6e76b9ca7b99dfd5591d7719c5807e2181387921d61',\n"
)
ADDITION = (
    b"              // Linked-context Agent candidate; keep the active Release 72 digest.\n"
    b"              '3d7ea2e60ffefa01c6a2bc99d5b5fdb29cc989031a027864a2e9d1acc68a35b6',\n"
)
EXPECTED_BLOB = "31b7839efd53f8533739d66497358aec8809938b"


def git_blob(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def main() -> None:
    protected_base = subprocess.check_output(["git", "show", f"HEAD:{PATH}"])
    assert git_blob(protected_base) == BASE_BLOB, "protected-base workflow changed"
    assert protected_base.count(ANCHOR) == 1, "Release 72 policy anchor changed"
    assert ADDITION not in protected_base, "candidate policy already present"
    candidate = protected_base.replace(ANCHOR, ANCHOR + ADDITION, 1)
    actual = git_blob(candidate)
    assert actual == EXPECTED_BLOB, f"candidate workflow blob mismatch: {actual}"
    print(f"verified complete candidate Review workflow Git blob: {actual}")


if __name__ == "__main__":
    main()
