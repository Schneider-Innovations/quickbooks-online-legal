import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const workflow = readFileSync(
  new URL('../.github/workflows/codex-cli-review-receipt.yml', import.meta.url),
  'utf8',
);

const match = workflow.match(/const cleanReviewLinePattern =\s*(\/[^\n]+\/i);/);
assert.ok(match, 'workflow must define the bounded clean-review pattern');
const cleanReviewLinePattern = Function(`return ${match[1]}`)();
const reviewedCommitLinePattern = /^\*\*Reviewed commit:\*\*\s*`[0-9a-f]{7,40}`$/i;
const isCleanReview = (body) => {
  const substantiveLines = body.split(/\r?\n/)
    .map((line) => line.trim()).filter(Boolean);
  return substantiveLines.length >= 2 &&
    cleanReviewLinePattern.test(substantiveLines[0]) &&
    reviewedCommitLinePattern.test(substantiveLines[1]);
};

test('accepts documented Connector clean templates', () => {
  for (const firstLine of [
    'No major issues found.',
    'Codex Review: Did not find any major issues.',
    "Codex Review: Didn't find any major issues. Another round soon, please!",
    'Codex Review: Didn’t find any major issues. Already looking forward to the next diff.',
    "Codex Review: Didn't find any major issues. Delightful!",
    "Codex Review: Didn't find any major issues. Chef's kiss.",
    "Codex Review: Didn't find any major issues. :+1:",
  ]) {
    assert.equal(isCleanReview(`${firstLine}\n\n**Reviewed commit:** \`abcdef1234\``), true);
  }
});

test('rejects unrecognized or ambiguous clean prose', () => {
  for (const body of [
    "I didn't find any major issues because I couldn't review the code.\n\n**Reviewed commit:** \`abcdef1234\`",
    'It is incorrect to say I did not find any major issues.\n\n**Reviewed commit:** `abcdef1234`',
    "Codex Review: Didn't find any major issues. Found a critical authentication flaw.\n\n**Reviewed commit:** \`abcdef1234\`",
    "Codex Review: Didn't find any major issues.\nFound a critical authentication flaw.\n**Reviewed commit:** \`abcdef1234\`",
    "Codex Review: Didn't find any major issues in the documentation.\n\n**Reviewed commit:** \`abcdef1234\`",
    "Codex Review: Didn't find any major issues.\n\nReviewed commit: abcdef1234",
  ]) {
    assert.equal(isCleanReview(body), false);
  }
});
