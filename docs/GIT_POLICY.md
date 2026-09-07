# Single-main-tree Git policy

NeuCLX has one continuously growing tree: `main`.

- No feature, release, experiment, or parallel branches.
- No pull-request development flow.
- Every accepted change is a forward-only commit on `main`.
- Force-pushes and history rewrites are forbidden.
- CI/CD receives `GITHUB_REF` and `GITHUB_EVENT_NAME`; `scripts/enforce_main_only.py` fails unless they are exactly `refs/heads/main` and `push`.
- A failed experiment is preserved honestly by a forward corrective commit, never erased from history.

Repository-side branch protection should additionally deny branch creation where the GitHub plan and ruleset permissions support it. The checked-in CI guard is the portable enforcement layer.
