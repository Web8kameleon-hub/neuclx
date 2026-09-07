"""Minimal PEP 517 backend, intentionally dependency-free."""

from pathlib import Path
import base64
import csv
import hashlib
import io
import zipfile


def _wheel_name():
    return "neuclx-0.1.0-py3-none-any.whl"


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    target = Path(wheel_directory) / _wheel_name()
    files = {}
    for path in Path("src/neuclx").glob("*.py"):
        files[f"neuclx/{path.name}"] = path.read_bytes()
    dist = "neuclx-0.1.0.dist-info"
    files[f"{dist}/METADATA"] = b"Metadata-Version: 2.1\nName: neuclx\nVersion: 0.1.0\n"
    files[f"{dist}/WHEEL"] = b"Wheel-Version: 1.0\nGenerator: neuclx_build\nRoot-Is-Purelib: true\nTag: py3-none-any\n"
    rows = []
    for name, data in files.items():
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
        rows.append((name, f"sha256={digest}", str(len(data))))
    record = io.StringIO()
    writer = csv.writer(record, lineterminator="\n")
    writer.writerows(rows + [(f"{dist}/RECORD", "", "")])
    files[f"{dist}/RECORD"] = record.getvalue().encode()
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    return target.name

