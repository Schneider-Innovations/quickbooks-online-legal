"""Verify three source-bound mirror reconstructions and exact additive admission."""
import hashlib, json, pathlib, re, runpy, subprocess
ROOT = pathlib.Path(__file__).resolve().parents[1]
PROOF = json.loads((ROOT / 'tests/review-128-local-mirrors-proof.json').read_bytes())
PATH = '.github/workflows/codex-cli-review-receipt.yml'
ADMISSION = '.github/workflows/review-approved-pin-local.yml'
EXPECTED = {'f6e3007283ef4be2bbae85a7481a92fed012a0a0',
            'f41984cb707ff0a52a3a23f3d1cd5c21245ddd83',
            '9a67fa62fcfebb30ab52e23176917976c7697955'}
REFS = {'0d22980fabed811ff5ed7be85d1bc12e8bbdd3b3',
        '8a6bb0fe5daa478204346cf3f8f5be1fd3298007'}
def main():
    assert PROOF['schema'] == 'review-source-bound-local-admission/v2'
    base_sha = PROOF['protected_base_commit']
    assert re.fullmatch('[0-9a-f]{40}', base_sha)
    git = lambda path: subprocess.check_output(['git', 'show', base_sha + ':' + path], cwd=ROOT)
    base = git(PATH)
    helper = runpy.run_path(str(ROOT / 'tests/verify_review_81_local_blob.py'))
    assert helper['git_blob'](base) == PROOF['base_blob']
    assert hashlib.sha256(base).hexdigest() == PROOF['base_sha256']
    assert (ROOT / PATH).read_bytes() == base, 'running caller must stay unchanged'
    assert {row['blob'] for row in PROOF['mirrors']} == EXPECTED
    for row in PROOF['mirrors']:
        patch = (ROOT / row['patch']).read_bytes()
        assert hashlib.sha256(patch).hexdigest() == row['patch_sha256']
        candidate = helper['apply_patch'](base, patch)
        assert len(candidate) == row['bytes']
        assert helper['git_blob'](candidate) == row['blob']
        assert hashlib.sha256(candidate).hexdigest() == row['sha256']
        assert (ROOT / row['complete_source_fixture']).read_bytes() == candidate
    before, after = git(ADMISSION), (ROOT / ADMISSION).read_bytes()
    assert hashlib.sha256(before).hexdigest() == PROOF['admission_before_sha256']
    assert hashlib.sha256(after).hexdigest() == PROOF['admission_after_sha256']
    def block(data, name):
        match = re.search(rb'(?m)^      ' + name + rb': [|]\n((?:        [^\n]+\n)+)', data)
        assert match
        entries = match[1].splitlines()
        assert len(entries) == len(set(entries))
        return match[1], {entry.strip() for entry in entries}
    normalized = after
    for name, expected in [
        (b'APPROVED_LOCAL_WORKFLOW_BLOBS', {('Schneider-Innovations/' + repo + '=' + blob).encode()
          for repo in ('amazon-store-outpost-legal', 'quickbooks-online-legal') for blob in EXPECTED}),
        (b'APPROVED_REUSABLE_REFS', {ref.encode() for ref in REFS})]:
        old_block, old = block(before, name)
        new_block, new = block(after, name)
        assert not old - new
        assert new - old == expected
        normalized = normalized.replace(new_block, old_block, 1)
    assert normalized == before, 'non-admission bytes changed'
    print('verified three complete mirrors, six exact blob entries, and two exact reusable refs')
if __name__ == '__main__':
    main()
