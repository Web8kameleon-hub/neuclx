# Single-main-tree Git policy

NeuCLX has one continuously growing tree: `main`.

- No feature, release, experiment, or parallel branches.
- No pull-request development flow.
- Every accepted change is a forward-only commit on `main`.
- Force-pushes and history rewrites are forbidden.
- CI/CD accepts direct pushes only to `refs/heads/main`; branches, tags, pull requests, and other refs are rejected.
- Per-commit candidate artifacts and attestations are generated from `main`; no release tag is created.
- A failed experiment is preserved honestly by a forward corrective commit, never erased from history.

Repository-side branch protection should additionally deny branch creation where the GitHub plan and ruleset permissions support it. The checked-in CI guard is the portable enforcement layer.
