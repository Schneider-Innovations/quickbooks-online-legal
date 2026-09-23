const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const AsyncFunction = (async function () {}).constructor;

const workflow = fs.readFileSync(path.join(__dirname, '..', '.github', 'workflows',
  'codex-review-receipt-caller.yml'), 'utf8').split(/\r?\n/);
const step = workflow.findIndex((line) => line.includes('name: Reconcile only a verified synthetic merge invalidation'));
assert(step >= 0);
const scriptStart = workflow.findIndex((line, index) => index > step && line === '          script: |');
assert(scriptStart > step);
const script = [];
for (const line of workflow.slice(scriptStart + 1)) {
  if (!line.startsWith('            ')) break;
  script.push(line.slice(12));
}
const runScript = new AsyncFunction('github', 'context', 'core', 'process', script.join('\n'));

const owner = 'Schneider-Innovations';
const repo = 'quickbooks-online-legal';
const number = 91;
const head = 'a'.repeat(40);
const base = 'b'.repeat(40);
const merge = 'c'.repeat(40);
const tree = 'd'.repeat(40);
const runId = 1234;
const markerRunId = 1200;
const label = 'ready-for-final-review';
const requestTime = '2026-09-23T09:02:00Z';
const markerTime = '2026-09-23T09:01:00Z';

async function scenario(options = {}) {
  const failures = [];
  const updates = [];
  const pr = {
    state: 'open', draft: false, number,
    base: { ref: 'main', sha: base },
    head: { sha: head, repo: { full_name: `${owner}/${repo}` } },
    labels: [{ name: label }],
  };
  const receipt = {
    id: 10, name: 'ai-review/receipt', app: { id: 15368 }, status: 'completed', conclusion: 'success',
    external_id: `ai-cli-review:${number}:${head}:run:${runId}:1234567890123`,
    output: { text: JSON.stringify({ status: 'completed', decision: 'PASS', analysis_complete: true,
      repository: `${owner}/${repo}`, pr_number: number, head_sha: head, base_sha: base,
      merge_sha: merge, trusted_binding: { repository: `${owner}/${repo}`, pr_number: number,
        head_sha: head, base_sha: base, reviewed_merge_sha: merge, merge_tree_sha: tree } }) },
  };
  const marker = {
    id: 20, name: 'ai-review/receipt', app: { id: 15368 }, status: 'completed', conclusion: 'failure',
    external_id: `ai-review-invalidated:merge:${number}:${head}:${merge}:${markerRunId}`,
    completed_at: options.lateMarker ? '2026-09-23T09:03:00Z'
      : options.afterLabelMarker ? '2026-09-23T09:01:59.500Z' : markerTime,
    output: { title: 'Final-head AI review required' },
  };
  const headChecks = [receipt, ...['ai-review/execution', 'ai-review/verdict'].map((name, index) => ({
    id: 30 + index, name, app: { id: 15368 }, status: 'completed', conclusion: 'success',
    external_id: `${name}:${number}:${head}:${merge}:${runId}:head`,
  }))];
  const readyEvent = { id: 50, event: 'labeled', label: { name: label },
    actor: { login: options.unauthorizedRelabel ? 'other-user' : 'mercury1231' },
    created_at: options.unauthorizedRelabel ? '2026-09-23T09:03:00Z' : '2026-09-23T09:01:59Z' };
  const readyHistory = options.sameSecondRelabel ? [
    { id: 52, event: 'labeled', label: { name: label }, actor: { login: 'mercury1231' },
      created_at: requestTime },
    { id: 51, event: 'unlabeled', label: { name: label }, actor: { login: 'mercury1231' },
      created_at: requestTime },
    readyEvent,
  ] : [readyEvent];
  const checksList = async () => {};
  const issueEvents = async () => {};
  const github = {
    paginate: async (method, args) => method === checksList
      ? (args.ref === head ? headChecks : [marker]) : readyHistory,
    rest: {
      pulls: { get: async () => ({ data: pr }) },
      checks: { listForRef: checksList, update: async (args) => updates.push(args) },
      issues: { listEvents: issueEvents },
      git: { getRef: async () => ({ data: { object: { sha: merge } } }) },
      repos: { getCommit: async () => ({ data: { parents: [{ sha: base }, { sha: head }],
        commit: { tree: { sha: tree } } } }) },
      actions: { getWorkflowRun: async ({ run_id }) => ({ data: {
        path: '.github/workflows/codex-review-receipt-caller.yml', event: 'pull_request_target',
        actor: { login: 'mercury1231' },
        created_at: run_id === runId ? requestTime : '2026-09-23T09:00:00Z',
      } }) },
    },
  };
  const context = { repo: { owner, repo }, runId, eventName: 'pull_request_target',
    actor: 'mercury1231', payload: { action: 'labeled', label: { name: label },
      pull_request: { number, head: { sha: head } } } };
  const core = { setFailed: (message) => failures.push(message), notice: () => {} };
  await runScript(github, context, core, { env: { PR_NUMBER: '0', AUTOMATION_LOGIN: 'mercury1231' } });
  return { failures, updates };
}

(async () => {
  const valid = await scenario();
  assert.deepEqual(valid.failures, []);
  assert.equal(valid.updates.length, 1);
  assert.equal(valid.updates[0].conclusion, 'neutral');

  const late = await scenario({ lateMarker: true });
  assert.deepEqual(late.failures, ['AI_REVIEW_RECONCILE_MARKER_NOT_PRIOR_TO_REQUEST']);
  assert.equal(late.updates.length, 0);

  const afterLabel = await scenario({ afterLabelMarker: true });
  assert.deepEqual(afterLabel.failures, ['AI_REVIEW_RECONCILE_LABEL_EVENT_CHANGED']);
  assert.equal(afterLabel.updates.length, 0);

  const relabeled = await scenario({ unauthorizedRelabel: true });
  assert.deepEqual(relabeled.failures, ['AI_REVIEW_RECONCILE_LABEL_EVENT_CHANGED']);
  assert.equal(relabeled.updates.length, 0);
  const sameSecond = await scenario({ sameSecondRelabel: true });
  assert.deepEqual(sameSecond.failures, ['AI_REVIEW_RECONCILE_LABEL_EVENT_CHANGED']);
  assert.equal(sameSecond.updates.length, 0);
  console.log('review reconciliation: prior marker accepted; later markers and re-label denied');
})().catch((error) => { console.error(error); process.exitCode = 1; });
