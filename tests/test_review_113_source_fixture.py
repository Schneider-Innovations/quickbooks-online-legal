"""A future mirror's complete source must exist and match reconstruction."""
import hashlib
import json
from pathlib import Path
import runpy
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent


class CandidateSourceFixtureTests(unittest.TestCase):
    def setUp(self):
        self.verifier = runpy.run_path(str(HERE / 'verify_review_113_local_blob.py'))
        self.function = self.verifier['main']
        self.proof = self.verifier['PROOF']
        helper = runpy.run_path(str(HERE / 'verify_review_81_local_blob.py'))
        base = subprocess.check_output([
            'git', 'show', self.proof['protected_base_commit'] + ':' + self.proof['workflow_path']],
            cwd=HERE.parent)
        self.candidate = helper['apply_patch'](base, (HERE / 'review-113-local-mirror.patch').read_bytes())
        self.directory = tempfile.TemporaryDirectory(prefix='qbo-review113-fixture-')
        self.addCleanup(self.directory.cleanup)
        self.temporary = Path(self.directory.name)
        for name in ('verify_review_81_local_blob.py', 'review-113-local-mirror.patch'):
            shutil.copyfile(HERE / name, self.temporary / name)
        (self.temporary / 'fixtures').mkdir()
        self.fixture = self.temporary / 'fixtures/review-113-local-mirror.yml'

    def verify(self):
        with patch.dict(self.function.__globals__, {'HERE': self.temporary}):
            self.function()

    def test_missing_candidate_source_refuses_admission_proof(self):
        with self.assertRaises((FileNotFoundError, AssertionError)):
            self.verify()

    def test_damaged_candidate_source_refuses_admission_proof(self):
        self.fixture.write_bytes(self.candidate[:-1] + b'!')
        with self.assertRaises(AssertionError):
            self.verify()

    def test_complete_exact_candidate_source_is_verified(self):
        self.fixture.write_bytes(self.candidate)
        self.verify()
        self.assertEqual(hashlib.sha256(self.fixture.read_bytes()).hexdigest(),
                         self.proof['candidate_sha256'])


if __name__ == '__main__':
    unittest.main()
