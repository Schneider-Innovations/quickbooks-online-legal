import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const workflow = readFileSync(
  new URL('../.github/workflows/codex-cli-review-receipt.yml', import.meta.url),
  'utf8',
);

const match = workflow.match(/const cleanReviewPattern =\s*(\/[^\n]+\/i);/);
assert.ok(match, 'workflow must define the bounded clean-review pattern');
const cleanReviewPattern = Function(`return ${match[1]}`)();

test('accepts documented Connector clean templates', () => {
  for (const phrase of [
    'No major issues found.',
    'Did not find any major issues.',
    "Didn't find any major issues.",
    'Didn’t find any major issues.',
  ]) {
    assert.match(phrase, cleanReviewPattern);
  }
});

test('rejects unrecognized or ambiguous clean prose', () => {
  for (const phrase of [
    'No blocker observed.',
    'Major issues were not found.',
    'No major issue found.',
  ]) {
    assert.doesNotMatch(phrase, cleanReviewPattern);
  }
});
