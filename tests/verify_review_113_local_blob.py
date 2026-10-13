"""Verify complete generated R113 bytes and additive source admission only."""
import hashlib
import json
from pathlib import Path
import re
import runpy
import subprocess

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
PROOF = json.loads((HERE / 'review-113-local-mirror-proof.json').read_bytes())

def main():
    base = subprocess.check_output(['git', 'show', PROOF['protected_base_commit'] + ':' + PROOF['workflow_path']], cwd=ROOT)
    helper = runpy.run_path(str(HERE / 'verify_review_81_local_blob.py'))
    assert helper['git_blob'](base) == PROOF['base_blob']
    assert hashlib.sha256(base).hexdigest() == PROOF['base_sha256']
    patch = (HERE / 'review-113-local-mirror.patch').read_bytes()
    changes = [line for line in patch.splitlines() if line.startswith((b'+', b'-')) and not line.startswith((b'+++', b'---'))]
    expected = [b"+              '" + digest.encode() + b"'," for digest in PROOF['added_policy_digests']]
    assert changes == expected, 'complete generated mirror diff must add only these two digests'
    candidate = helper['apply_patch'](base, patch)
    assert len(candidate) == PROOF['candidate_bytes']
    assert helper['git_blob'](candidate) == PROOF['candidate_blob']
    assert hashlib.sha256(candidate).hexdigest() == PROOF['candidate_sha256']
    # Admission must not replace the caller that protected main executes.
    assert (ROOT / PROOF['workflow_path']).read_bytes() == base
    approved = (ROOT / PROOF['admission_path']).read_bytes()
    previous = subprocess.check_output(['git', 'show', PROOF['protected_base_commit'] + ':' + PROOF['admission_path']], cwd=ROOT)
    entries = lambda value: set(re.findall(rb'Schneider-Innovations/[a-z0-9-]+=[0-9a-f]{40}', value))
    expected_new = {('Schneider-Innovations/' + repo + '=' + PROOF['candidate_blob']).encode() for repo in PROOF['admitted_repositories']}
    assert entries(previous) <= entries(approved)
    assert entries(approved) - entries(previous) == expected_new
    assert hashlib.sha256(approved).hexdigest() == PROOF['admission_after_sha256']
    print('verified generated R113 candidate and add-only source admission:', PROOF['candidate_blob'])

if __name__ == '__main__':
    main()
