import hashlib
import json
from pathlib import Path

ALLOWED = {"copy", "adapt", "reference", "reject", "unavailable"}


def canonical_content_sha256(content):
    content = content.replace(b"\r\n", b"\n")
    return hashlib.sha256(content).hexdigest()


def canonical_sha256(path):
    return canonical_content_sha256(path.read_bytes())


def validate(root=Path(".")):
    manifest = json.loads((root / "imports/manifest.json").read_text())
    sources = manifest["sources"]
    errors = []
    repos = set()
    hashes = set()
    if len(sources) != 16:
        errors.append(f"expected 16 sources, found {len(sources)}")
    for item in sources:
        repo = item["repository"]
        if repo in repos:
            errors.append(f"duplicate repository: {repo}")
        repos.add(repo)
        if item["decision"] not in ALLOWED:
            errors.append(f"invalid decision: {repo}")
        if item["decision"] == "copy":
            path = root / item["destination"]
            if not path.is_file():
                errors.append(f"missing copied candidate: {path}")
            else:
                actual = canonical_sha256(path)
                if actual != item["sha256"]:
                    errors.append(f"digest mismatch: {path}")
                if actual in hashes:
                    errors.append(f"duplicate content: {path}")
                hashes.add(actual)
            if item["visibility"] != "public":
                errors.append(f"private source exposed: {repo}")
            if not item.get("source_blob_sha"):
                errors.append(f"missing source blob: {repo}")
    return errors


if __name__ == "__main__":
    problems = validate()
    if problems:
        raise SystemExit("\n".join(problems))
    print("16-repository manifest valid; copied candidates unique and provenance-bound")
