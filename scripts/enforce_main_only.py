"""Fail CI/CD for every ref or event that is not a direct main update."""

import os
import sys

ALLOWED_REF = "refs/heads/main"
ALLOWED_EVENT = "push"


def validate(ref: str, event: str, head_ref: str = "") -> tuple[bool, str]:
    if event != ALLOWED_EVENT:
        return False, f"NeuCLX accepts direct main growth only; event {event!r} is forbidden"
    if ref == ALLOWED_REF:
        return True, "NeuCLX single-main-tree policy satisfied"
    if ref.startswith("refs/heads/"):
        return False, f"NeuCLX is a single tree: branch {ref!r} is forbidden"
    if ref.startswith("refs/tags/"):
        return False, f"NeuCLX accepts only {ALLOWED_REF}; tag {ref!r} is forbidden"
    return False, f"Git ref {ref!r} is forbidden"


def main() -> int:
    ok, message = validate(os.environ.get("NEUCLX_GIT_REF", ""), os.environ.get("NEUCLX_EVENT", ""), os.environ.get("NEUCLX_HEAD_REF", ""))
    print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
