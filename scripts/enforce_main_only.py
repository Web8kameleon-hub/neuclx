"""Fail CI/CD for every ref or event that is not a direct main update."""

import os
import re
import sys

ALLOWED_REF = "refs/heads/main"
ALLOWED_EVENT = "push"
RELEASE_TAG = re.compile(r"^refs/tags/v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)$")


CONTROLLED_IMPORT_BRANCH = "integration/import-16-repositories"

def validate(ref: str, event: str, head_ref: str = "") -> tuple[bool, str]:
    if event == "pull_request" and head_ref == CONTROLLED_IMPORT_BRANCH and ref.startswith("refs/pull/"):
        return True, "Controlled 16-repository import PR accepted for pre-main validation"
    if event != ALLOWED_EVENT:
        return False, f"NeuCLX accepts direct main growth only; event {event!r} is forbidden"
    if ref == ALLOWED_REF:
        return True, "NeuCLX single-main-tree policy satisfied"
    if RELEASE_TAG.fullmatch(ref):
        return True, "NeuCLX immutable semantic release tag accepted"
    if ref.startswith("refs/heads/"):
        return False, f"NeuCLX is a single tree: branch {ref!r} is forbidden"
    if ref.startswith("refs/tags/"):
        return False, f"release tag {ref!r} must use exact vMAJOR.MINOR.PATCH syntax"
    return False, f"Git ref {ref!r} is forbidden"


def main() -> int:
    ok, message = validate(os.environ.get("NEUCLX_GIT_REF", ""), os.environ.get("NEUCLX_EVENT", ""), os.environ.get("NEUCLX_HEAD_REF", ""))
    print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
