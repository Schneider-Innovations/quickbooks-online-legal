"""Verify complete reconstructed mirror bytes and the exact additive admission delta."""
import hashlib, json, pathlib, re, runpy, subprocess
ROOT = pathlib.Path(__file__).resolve().parents[1]
HERE = pathlib.Path(__file__).resolve().parent
PROOF = json.loads((HERE / 'review-125-local-mirrors-proof.json').read_bytes())
PATH = '.github/workflows/codex-cli-review-receipt.yml'
ADMISSION = '.github/workflows/review-approved-pin-local.yml'
BLOBS = {'historical': 'fb2d02598911677ee916134e586f2669e0e5a566',
         'policy': '6247f20b7c56979d023a2e93a5649c28a883bd67'}
POLICY = 'f635db7575c352732fd0303666030cefe246dc4cc97841a19a23fb3c18c63ee5'

def git(path):
    assert re.fullmatch('[0-9a-f]{40}', PROOF['protected_base_commit'])
    return subprocess.check_output(['git', 'show', PROOF['protected_base_commit'] + ':' + path],
        cwd=ROOT, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))

def block(data):
    match = re.search(rb'(?m)^      APPROVED_LOCAL_WORKFLOW_BLOBS: [|]\n((?:        [^\n]+\n)+)', data)
    assert match
    lines = match[1].splitlines()
    assert len(lines) == len(set(lines))
    assert all(re.fullmatch(rb'        Schneider-Innovations/[a-z0-9-]+=[0-9a-f]{40}', line) for line in lines)
    return match[1], {line.strip() for line in lines}

def main():
    assert PROOF['schema'] == 'review-source-bound-local-admission/v1'
    assert PROOF['policy_digest'] == POLICY
    helper = runpy.run_path(str(HERE / 'verify_review_81_local_blob.py'))
    base = git(PATH)
    assert helper['git_blob'](base) == PROOF['base_blob']
    assert hashlib.sha256(base).hexdigest() == PROOF['base_sha256']
    assert subprocess.check_output(['git', 'show', 'HEAD:' + PATH], cwd=ROOT, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)) == base
    subprocess.run(['git', 'diff', '--quiet', 'HEAD', '--', PATH], cwd=ROOT, check=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    assert {row['kind']: row['blob'] for row in PROOF['mirrors']} == BLOBS
    for row in PROOF['mirrors']:
        patch = (HERE / ('review-125-' + row['kind'] + '-mirror.patch')).read_bytes()
        assert patch.startswith(('--- a/' + PATH + '\n+++ b/' + PATH + '\n').encode())
        assert hashlib.sha256(patch).hexdigest() == row['patch_sha256']
        if row['kind'] == 'policy':
            changes = [line for line in patch.splitlines() if line[:1] in (b'+', b'-') and not line.startswith((b'+++', b'---'))]
            assert changes == [("+              '" + POLICY + "',").encode()]
        result = helper['apply_patch'](base, patch)
        assert len(result) == row['bytes']
        assert helper['git_blob'](result) == row['blob']
        assert hashlib.sha256(result).hexdigest() == row['sha256']
    before, after = git(ADMISSION), (ROOT / ADMISSION).read_bytes()
    assert hashlib.sha256(before).hexdigest() == PROOF['admission_before_sha256']
    assert hashlib.sha256(after).hexdigest() == PROOF['admission_after_sha256']
    old_block, old_entries = block(before)
    new_block, new_entries = block(after)
    expected = {('Schneider-Innovations/' + repo + '=' + blob).encode()
        for repo in ('amazon-store-outpost-legal', 'quickbooks-online-legal') for blob in BLOBS.values()}
    assert not old_entries - new_entries
    assert new_entries - old_entries == expected
    assert after.replace(new_block, old_block, 1) == before, 'non-admission bytes changed'
    print('verified two complete mirror reconstructions and exact four-entry additive admission')

if __name__ == '__main__':
    main()
