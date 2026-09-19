# AI review and merge requirements

The review workflow evaluates the current pull-request head and its merge preview against the protected base.

Required checks have separate meanings:

- `ai-review/execution`: the reviewer produced a trustworthy result for the requested revision.
- `ai-review/verdict`: that result satisfies the review policy. Successful execution alone does not permit merging.
- `review-allowlist/approved-pin`: the review workflow is an approved immutable version.
- `ai-review/receipt`: retained as a compatibility and stale-result safeguard during the migration.

An execution failure is an operational problem, not evidence that the proposed code contains a defect. A blocked verdict requires inspecting the review result. Neither condition may be treated as an approval.

When the pull request is stable and not a draft, the authorized review requester applies `ready-for-final-review`. Changes to the proposed revision or protected base can invalidate earlier results and require another review. Do not reuse approval for a different revision or remove required checks to make an ordinary pull request mergeable.

The public repository keeps an exact local copy of the approved Quality Gate workflow. Release updates admit the new workflow before activating it.
