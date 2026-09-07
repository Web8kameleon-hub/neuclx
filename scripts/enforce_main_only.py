"""Fail CI/CD for every ref or event that is not a direct main update."""

import os
import sys

ALLOWED_REF = "refs/heads/main"
ALLOWED_EVENT = "push"


def validate(ref: str, event: str) -> tuple[bool, str]:
    if ref != ALLOWED_REF:
        return False, f"NeuCLX is a single tree: {ref!r} is forbidden; only {ALLOWED_REF!r} is allowed"
    if event != ALLOWED_EVENT:
        return False, f"NeuCLX accepts direct main growth only; event {event!r} is forbidden"
    return True, "NeuCLX single-main-tree policy satisfied"


def main() -> int:
    ok, message = validate(os.environ.get("NEUCLX_GIT_REF", ""), os.environ.get("NEUCLX_EVENT", ""))
    print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
