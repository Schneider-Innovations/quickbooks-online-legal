const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

// The local review workflow (QG 27cf403 mirror) fails "Prepare isolated CLI
// review" with AI_CLI_REVIEW_REQUEST_GENERATION_INVALID unless the caller
// passes an exact `runId:attempt` request generation.
const root = path.join(__dirname, '..', '.github', 'workflows');
const read = (name) => fs.readFileSync(path.join(root, name), 'utf8').replace(/\r\n/g, '\n');
const caller = read('codex-review-receipt-caller.yml');
const local = read('codex-cli-review-receipt.yml');

const jobStart = caller.indexOf('\n  request-and-verify-review:\n');
const jobEnd = caller.indexOf('\n  reconcile-merge-invalidation:\n');
assert(jobStart >= 0 && jobEnd > jobStart);
const job = caller.slice(jobStart, jobEnd);
assert.match(job, /\n    needs: admit-review-request\n/);
assert.match(job, /\n    uses: \.\/\.github\/workflows\/codex-cli-review-receipt\.yml\n/);
const inputs = job.match(/\n      request_generation: .+/g) || [];
assert.equal(inputs.length, 1);
assert.equal(inputs[0].trim(),
  "request_generation: ${{ format('{0}:{1}', github.run_id, github.run_attempt) }}");

assert.match(local, /\n      request_generation:\n/);
assert.match(local, /AI_CLI_REVIEW_REQUEST_GENERATION_INVALID/);
console.log('review request generation: caller passes runId:attempt to the local review workflow');
