"""Reconstruct the exact admitted local Review workflow from protected-base bytes."""

import hashlib
import subprocess


PATH = ".github/workflows/codex-cli-review-receipt.yml"
OLD = b"              '15439fbc929894254187a5f068b3f96ebdead087b24afe0419a4c3b40b12f9b2',\n"
ADDITION = (
    b"              // Release 59 candidate policy: admitted before activation.\n"
    b"              '487b8e2d43db74160c50b6e76b9ca7b99dfd5591d7719c5807e2181387921d61',\n"
)
EXPECTED_BLOB = "40dd0e5e977f3acfb5e90ea662856e613aeae190"


def main() -> None:
    source = subprocess.check_output(["git", "show", f"HEAD:{PATH}"])
    assert source.count(OLD) == 1, "protected-base policy anchor changed"
    candidate = source.replace(OLD, OLD + ADDITION, 1)
    actual = hashlib.sha1(f"blob {len(candidate)}\0".encode() + candidate).hexdigest()
    assert actual == EXPECTED_BLOB, f"candidate blob mismatch: {actual}"
    print(f"verified exact candidate Git blob: {actual}")


if __name__ == "__main__":
    main()
