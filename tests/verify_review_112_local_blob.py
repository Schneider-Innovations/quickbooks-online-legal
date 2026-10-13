"""Verify the complete R112 mirror diff before admitting its exact Git blob.

The patch adds only R112's policy digest to the already admitted protected-base
mirror. It does not publish the caller, activate the Agent or bypass old checks.
"""
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
PROOF = json.loads((HERE / 'review-112-local-mirror-proof.json').read_bytes())
PATCH = HERE / 'review-112-local-mirror.patch'


def main():
    flags = {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {}
    base = subprocess.check_output(
        ['git', 'show', f"{PROOF['protected_base_commit']}:{PROOF['workflow_path']}"],
        cwd=ROOT, **flags,
    )
    legacy = runpy.run_path(str(HERE / 'verify_review_81_local_blob.py'))
    assert legacy['git_blob'](base) == PROOF['base_blob']
    assert hashlib.sha256(base).hexdigest() == PROOF['base_sha256']
    patch = PATCH.read_bytes()
    changes = [line for line in patch.splitlines() if line.startswith((b'+', b'-')) and not line.startswith((b'+++', b'---'))]
    expected = b"+              '" + PROOF['extra_policy_digest'].encode() + b"',"
    assert changes == [expected], 'R112 must add exactly one compatibility digest'
    candidate = legacy['apply_patch'](base, patch)
    assert len(candidate) == PROOF['candidate_bytes']
    assert legacy['git_blob'](candidate) == PROOF['candidate_blob']
    assert hashlib.sha256(candidate).hexdigest() == PROOF['candidate_sha256']
    approved = (ROOT / '.github/workflows/review-approved-pin-local.yml').read_text()
    for repo in ('amazon-store-outpost-legal', 'quickbooks-online-legal'):
        assert f"Schneider-Innovations/{repo}={PROOF['candidate_blob']}" in approved
    print('verified complete R112 candidate mirror:', PROOF['candidate_blob'])


if __name__ == '__main__':
    main()
